#!/usr/bin/env python3
"""Small, blinded host-only RARiS STF integrity benchmark (Python standard library)."""
import argparse
import collections
import hashlib
import json
import os
import random
import statistics
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from prepare import HEADER, FS_MAGIC, STF_MAGIC, inspect

ROOT = Path(__file__).resolve().parent
KINDS = ("missing", "duplicate", "reorder", "header_corruption")
REVISION = "ccf94e725389b5d32b2cd167312deb88c6461eba"
MODEL = "gpt-4.1-mini-2025-04-14"
INPUT_RATE, CACHED_RATE, OUTPUT_RATE = 0.40, 0.10, 1.60  # USD per million
PROMPT = """Inspect one independently framed NestDAQ SubTimeFrame v1 stream window.
Records are presented in observed order. Their indexes are local observed indexes,
not original positions. Window lengths vary: do not infer a fault from record count.
Use only supplied observations and the per-source reference derived from earlier
records. No labels, injection locations or original sequence are available.
STF header layout is little endian <QIHHIIIIQQ (48 bytes): magic, total length,
header length, type, timeframe ID, FEM type, FEM ID, message count, seconds,
microseconds. STF magic is 0x00454d4954425553. byte_count is independently observed
record length, not the length declared in the header. Header fields are decoded
without repair. payload_sha256 describes unchanged payload bytes.
Report evidence-supported missing, duplicate, reorder, header_corruption or
byte_volume candidates, with local observed indexes. A missing candidate is
anchored at the first observed record after the gap; duplicates at the later copy;
reorder at both swapped records; header corruption at its record. Missing means
an ID gap relative to reference step; an out-of-order continuous set is reorder,
not missing. Duplicated identical records are duplicate. Unexpected magic, length,
header length, stable FEM/type/message fields or usec outside [0,1000000) are
header_corruption candidates. byte_volume is length above reference threshold.
Do not infer detector bursts, event rate, expert-confirmed natural faults, or
cross-stream alignment. Untouched data may contain natural anomaly candidates.
Return only the required JSON; an empty alarms list means no supported candidate.
"""
ALARM_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"alarms": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "properties": {"kind": {"type": "string", "enum": list(KINDS) + ["byte_volume"]},
                       "indexes": {"type": "array", "items": {"type": "integer"}},
                       "evidence": {"type": "string"}},
        "required": ["kind", "indexes", "evidence"]}}}, "required": ["alarms"]}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def now():
    return datetime.now(timezone.utc).isoformat()


def observation(chunk, index):
    fields = HEADER.unpack_from(chunk)
    names = ("magic", "length", "header_length", "type", "timeframe_id", "fem_type",
             "fem_id", "messages", "time_sec", "time_usec")
    result = dict(zip(names, fields))
    result["magic"] = f"0x{fields[0]:016x}"
    return dict(index=index, byte_count=len(chunk), header_hex=chunk[:48].hex(),
                payload_sha256=hashlib.sha256(chunk[48:]).hexdigest(), **result)


def make_input(chunks, reference):
    # This allowlist is the only detector input. Never pass labels or provenance.
    return {"reference": reference, "records": [observation(c, i) for i, c in enumerate(chunks)]}


def reference_for(frames):
    steps = [(b["timeframe_id"] - a["timeframe_id"]) % (2**32)
             for a, b in zip(frames, frames[1:])]
    return dict(id_step=statistics.mode(steps),
                fem_type=statistics.mode(f["fem_type"] for f in frames),
                fem_id=statistics.mode(f["fem_id"] for f in frames),
                messages=statistics.mode(f["messages"] for f in frames), type=0,
                volume_threshold=3 * statistics.median(f["length"] for f in frames))


def header_bad(r, ref):
    return (r["magic"] != f"0x{STF_MAGIC:016x}" or r["header_length"] != 48
            or r["length"] != r["byte_count"] or r["length"] < 48
            or r["type"] != ref["type"] or r["fem_type"] != ref["fem_type"]
            or r["fem_id"] != ref["fem_id"] or r["messages"] != ref["messages"]
            or not 0 <= r["time_usec"] < 1_000_000)


def rules(blind, volume_only=False):
    rows, ref = blind["records"], blind["reference"]
    alarms = []
    def add(kind, indexes, evidence):
        alarms.append(dict(kind=kind, indexes=indexes, evidence=evidence))
    for r in rows:
        if r["byte_count"] > ref["volume_threshold"]:
            add("byte_volume", [r["index"]], "Observed record bytes exceed development threshold")
    if volume_only:
        return {"alarms": alarms}
    valid, seen = [], {}
    for r in rows:
        if header_bad(r, ref):
            add("header_corruption", [r["index"]], "STF header constraint mismatch")
            continue
        identity = (r["header_hex"], r["payload_sha256"], r["byte_count"])
        if identity in seen:
            add("duplicate", [r["index"]], "Identical observed record repeated")
        else:
            seen[identity] = r["index"]
            valid.append(r)
    # These short windows cannot cross uint32 wrap in this public run.
    for a, b in zip(valid, valid[1:]):
        if b["timeframe_id"] < a["timeframe_id"]:
            add("reorder", [a["index"], b["index"]], "Observed IDs decrease")
    ordered = sorted(valid, key=lambda r: r["timeframe_id"])
    for a, b in zip(ordered, ordered[1:]):
        if b["timeframe_id"] - a["timeframe_id"] > ref["id_step"]:
            # Do not report a gap explained by a malformed header record.
            between = rows[min(a["index"], b["index"]) + 1:max(a["index"], b["index"])]
            if not any(header_bad(r, ref) for r in between):
                add("missing", [b["index"]], "Sorted unique IDs have a gap")
    return {"alarms": alarms}


def inject(chunks, kind, position, variant):
    result = list(chunks)
    details = dict(kind=kind, original_local_index=position)
    if kind == "missing":
        details["removed_record_sha256"] = hashlib.sha256(result.pop(position)).hexdigest()
        targets = [position]
    elif kind == "duplicate":
        result.insert(position + 1, result[position])
        targets = [position + 1]
    elif kind == "reorder":
        result[position], result[position + 1] = result[position + 1], result[position]
        targets = [position, position + 1]
    else:
        chunk = bytearray(result[position])
        # Four intentionally invalid variants; do not claim all header failures covered.
        byte_offset, replacement = [(0, b"\x00"), (8, struct.pack("<I", len(chunk) + 8)),
                                    (12, struct.pack("<H", 47)),
                                    (40, struct.pack("<Q", 1_000_000))][variant % 4]
        details.update(header_byte_offset=byte_offset, before_hex=chunk[byte_offset:byte_offset+len(replacement)].hex(),
                       after_hex=replacement.hex())
        chunk[byte_offset:byte_offset+len(replacement)] = replacement
        result[position] = bytes(chunk)
        targets = [position]
    details["observed_target_indexes"] = targets
    return result, details


def download(data):
    for source in ("00", "01", "02"):
        p = data / source / "run000020.dat"
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://raw.githubusercontent.com/nobukoba/container-interfacing-nestdaq-eicrecon/{REVISION}/example_rawdata/raris_ac_lgad_202603/{source}/run000020.dat"
            with urllib.request.urlopen(url, timeout=60) as response:
                p.write_bytes(response.read())


def prepare(data, output):
    if (output / "freeze.json").exists():
        raise ValueError("Freeze already exists; use a new output directory for a new protocol")
    expected = read(ROOT / "results" / "summary.json")
    expected_hashes = {Path(s["file"]).parent.name: s["sha256"] for s in expected["sources"]}
    integrity, references, cases, labels, scans = [], {}, {}, {}, {}
    rng = random.Random(20261005)
    elapsed = time.perf_counter()
    for source in ("00", "01", "02"):
        path = data / source / "run000020.dat"
        metadata, frames = inspect(path)
        raw = path.read_bytes()
        if metadata["sha256"] != expected_hashes[source]:
            raise ValueError("Public input hash does not match archived inspection")
        # FileSink envelope checks in addition to prepare.inspect STF checks.
        if struct.unpack_from("<IH", raw, 8) != (304, 304) or raw[-304:-296] != b"FILETRL\0":
            raise ValueError("Unsupported or missing FileSink envelope")
        if struct.unpack_from("<IH", raw, len(raw)-296) != (304, 304):
            raise ValueError("Malformed FileSink trailer")
        cut = len(frames) // 2
        ref = reference_for(frames[:cut])
        references[source] = ref
        chunks = [raw[f["offset"]:f["offset"]+f["length"]] for f in frames]
        ids = [f["timeframe_id"] for f in frames]
        timestamps = [f["time_sec"]*1_000_000 + f["time_usec"] for f in frames]
        integrity.append(dict(source=source, sha256=metadata["sha256"], bytes=len(raw),
            frames=len(frames), development_frames=cut, evaluation_frames=len(frames)-cut,
            filesink_header_bytes=304, filesink_trailer_bytes=304, trailing_unparsed_bytes=0,
            id_delta_counts=dict(collections.Counter(b-a for a,b in zip(ids,ids[1:]))),
            timestamp_regressions=sum(b<a for a,b in zip(timestamps,timestamps[1:])),
            invalid_usec=sum(not 0<=f["time_usec"]<1_000_000 for f in frames),
            frame_size_min=min(map(len,chunks)), frame_size_max=max(map(len,chunks)),
            first_id=ids[0], last_id=ids[-1], frame_count_matches_prior=len(frames)==next(s["frames"] for s in expected["sources"] if Path(s["file"]).parent.name==source)))
        # 32-record non-overlapping second-half windows, including final partial.
        for start in range(cut, len(frames), 32):
            key = f"{source}-{start}"
            scans[key] = make_input(chunks[start:start+32], ref)
        # Development and evaluation windows are disjoint in original frame indexes.
        for phase, starts in (("development", [32]),
                              ("evaluation", sorted(rng.sample(list(range(cut, len(frames)-31, 32)), 4)))):
            for variant, start in enumerate(starts):
                original = chunks[start:start+32]
                for kind in ("untouched",) + KINDS:
                    changed, intervention = (original, None) if kind == "untouched" else inject(original, kind, rng.randint(5,24), variant)
                    case_id = hashlib.sha256(f"{phase}/{source}/{start}/{kind}".encode()).hexdigest()[:16]
                    cases[case_id] = dict(phase=phase, input=make_input(changed, ref))
                    labels[case_id] = dict(source=source, start_original_index=start,
                        end_original_index_exclusive=start+32, original_file_byte_offset=frames[start]["offset"],
                        original_frame_offsets=[f["offset"] for f in frames[start:start+32]],
                        kind=kind, intervention=intervention,
                        input_sha256=digest(cases[case_id]["input"]))
    if sum(s["frames"] for s in integrity) != 8470:
        raise ValueError("Unexpected total frame count")
    # Randomize detector case order. Opaque IDs do not encode kind or position.
    order = list(cases)
    rng.shuffle(order)
    cases = {k: cases[k] for k in order}
    protocol = dict(version=1, created_utc=now(), seed=20261005, window_records_before_mutation=32,
        development="first half per source; one window per source", evaluation="second half per source; four non-overlapping windows per source",
        expected_source_hashes=expected_hashes, source_revision=REVISION, references=references,
        model=MODEL, prompt=PROMPT, response_schema=ALARM_SCHEMA, max_output_tokens=1000,
        api=dict(endpoint="https://api.openai.com/v1/responses", temperature=0, store=False, retries=0, timeout_seconds=60),
        prices_usd_per_million=dict(input=INPUT_RATE, cached_input=CACHED_RATE, output=OUTPUT_RATE),
        pricing_source="https://developers.openai.com/api/docs/models/gpt-4.1-mini", pricing_checked_utc=now(),
        detection="Any alarm whose indexes intersect injected targets; classification additionally requires correct kind. No credit for unrelated alarms.",
        alarm_units="candidate alarms and windows with >=1 alarm; untouched alarms are not established false positives",
        baseline="existing development-median *3 byte-volume screen", structural_baseline="STF header validity, exact duplicates, ID order and gaps",
        api_scope="All 60 selected evaluation cases (48 injected + 12 untouched); broader untouched-half scan is conventional only",
        framing="Independent record boundaries from original valid STF parsing, retained through mutation. Header corruption does not destroy framing. Not an end-to-end byte-stream recovery test.",
        limitations=["Same-run halves, not an independent held-out run", "No natural fault truth or detector burst data", "Four synthetic header variants only", "Paired cases share base windows; counts are not independent samples", "No cross-source alignment claim", "No real-time DAQ throughput measurement", "No baseline results or injection labels supplied to AI"])
    write(output/"protocol.json", protocol)
    write(output/"inputs.json", cases)
    write(output/"labels.json", labels)
    write(output/"untouched-scan-inputs.json", scans)
    write(output/"integrity.json", dict(status="REPRODUCED_PUBLIC_DATA", checked_utc=now(), total_frames=8470,
          sources=integrity, elapsed_seconds=time.perf_counter()-elapsed,
          conclusion="Structural checks passed; this does not establish fault-free detector data."))
    files = ("protocol.json", "inputs.json", "labels.json", "untouched-scan-inputs.json")
    freeze = dict(frozen_utc=now(), files={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in files},
                  implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write(output/"freeze.json", freeze)
    print(json.dumps(dict(total_frames=8470, selected_cases=len(cases), evaluation_cases=sum(c["phase"]=="evaluation" for c in cases.values()), freeze_sha256=digest(freeze))))


def verify(output):
    freeze = read(output/"freeze.json")
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != freeze["implementation_sha256"]:
        raise ValueError("Implementation changed after freeze; use a new run")
    for name, expected in freeze["files"].items():
        if hashlib.sha256((output/name).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen artifact changed")
    return digest(freeze)


def measure_conventional(output):
    freeze_hash = verify(output)
    inputs = read(output/"inputs.json")
    results = {}
    for name, volume_only in (("byte_volume", True), ("structural_rules", False)):
        predictions = {}
        for case_id, case in inputs.items():
            start = time.perf_counter()
            prediction = rules(case["input"], volume_only)
            predictions[case_id] = dict(**prediction, elapsed_seconds=time.perf_counter()-start)
        scan_results = {}
        for case_id, blind in read(output/"untouched-scan-inputs.json").items():
            start = time.perf_counter()
            prediction = rules(blind, volume_only)
            scan_results[case_id] = dict(**prediction, elapsed_seconds=time.perf_counter()-start)
        results[name] = dict(cases=predictions, untouched_full_half_scan=scan_results)
    write(output/"conventional.json", dict(freeze_sha256=freeze_hash, measured_utc=now(), methods=results))
    report(output)


def cost(usage):
    cached = usage.get("input_tokens_details", {}).get("cached_tokens", 0)
    return ((usage["input_tokens"]-cached)*INPUT_RATE + cached*CACHED_RATE + usage["output_tokens"]*OUTPUT_RATE)/1_000_000


def request_body(blind, protocol):
    return dict(model=protocol["model"], instructions=protocol["prompt"], input=canonical(blind).decode(),
                temperature=0, store=False, max_output_tokens=protocol["max_output_tokens"],
                text={"format":dict(type="json_schema",name="stf_candidates",strict=True,schema=protocol["response_schema"])})


def validate_prediction(prediction, n):
    if set(prediction) != {"alarms"} or not isinstance(prediction["alarms"], list):
        raise ValueError("Invalid AI response")
    for a in prediction["alarms"]:
        if (set(a) != {"kind","indexes","evidence"} or a["kind"] not in KINDS+("byte_volume",)
            or not isinstance(a["evidence"], str) or not isinstance(a["indexes"], list)
            or not a["indexes"] or any(type(i) is not int or not 0<=i<n for i in a["indexes"])):
            raise ValueError("Invalid AI alarm")


def api_prediction(blind, protocol):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY is not set; use the documented hidden-input PowerShell procedure")
    request = urllib.request.Request(protocol["api"]["endpoint"], data=canonical(request_body(blind, protocol)),
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"}, method="POST")
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=protocol["api"]["timeout_seconds"]) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Never log response bodies, requests, headers, exception repr or credentials.
        return dict(status="http_error", http_status=error.code, elapsed_seconds=time.perf_counter()-start, usage=None)
    except (urllib.error.URLError, TimeoutError, OSError):
        return dict(status="transport_error", elapsed_seconds=time.perf_counter()-start, usage=None)
    elapsed = time.perf_counter()-start
    usage = result.get("usage")
    common = dict(elapsed_seconds=elapsed, usage=usage, actual_model=result.get("model"),
                  request_id=result.get("id"), input_sha256=digest(blind))
    if result.get("status") != "completed":
        return dict(status="incomplete", **common)
    try:
        texts = [item["text"] for entry in result["output"] for item in entry.get("content",[]) if item.get("type")=="output_text"]
        prediction = json.loads("".join(texts))
        validate_prediction(prediction,len(blind["records"]))
    except (KeyError, TypeError, ValueError):
        return dict(status="invalid_output", **common)
    # The key never appears in the model input. Defensive response redaction nonetheless.
    if key in json.dumps(prediction):
        return dict(status="redacted_output", **common)
    return dict(status="ok", **prediction, **common)


def run_api(output, phase, budget):
    frozen_hash = verify(output)
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set; no API request sent")
    protocol, inputs, labels = read(output/"protocol.json"),read(output/"inputs.json"),read(output/"labels.json")
    # Labels are only used by the orchestration selector; api_prediction receives blind input only.
    if phase=="pilot":
        selected = [k for k,c in inputs.items() if c["phase"]=="development" and labels[k]["source"]=="00"]
    else:
        pilot = read(output/"pilot-usage.json")
        if pilot["freeze_sha256"]!=frozen_hash or pilot["successful_cases"]!=5:
            raise ValueError("Successful frozen five-case pilot is required before evaluation")
        selected = [k for k,c in inputs.items() if c["phase"]=="evaluation"]
    path = output/("ai-"+phase+".json")
    saved = read(path) if path.exists() else dict(freeze_sha256=frozen_hash, phase=phase, started_utc=now(), cases={})
    if saved["freeze_sha256"] != frozen_hash:
        raise ValueError("API output belongs to a different freeze")
    # Conservative bound: at most one token per serialized UTF-8 byte plus 2048
    # protocol overhead tokens, and maximum output for every remaining request.
    remaining = [k for k in selected if k not in saved["cases"]]
    reserve = sum((len(canonical(request_body(inputs[k]["input"],protocol)))+2048)*INPUT_RATE/1e6
                  +protocol["max_output_tokens"]*OUTPUT_RATE/1e6 for k in remaining)
    spent = sum(cost(r["usage"]) for r in saved["cases"].values() if r.get("usage"))
    if reserve+spent>budget:
        raise ValueError("Conservative request cost reserve exceeds --budget-usd; no new request sent")
    print(json.dumps(dict(phase=phase,new_requests=len(remaining),estimated_upper_cost_usd=reserve+spent)),flush=True)
    for key in remaining:
        prediction = api_prediction(inputs[key]["input"],protocol)
        saved["cases"][key]=prediction
        write(path,saved)
        print(json.dumps(dict(case_id=key,status=prediction["status"],elapsed_seconds=prediction["elapsed_seconds"],
                             usage=prediction.get("usage"))),flush=True)
        if prediction["status"]!="ok":
            break  # Stop rather than silently dropping failures or retrying billed requests.
    usages=[r["usage"] for r in saved["cases"].values() if r.get("usage")]
    summary=dict(freeze_sha256=frozen_hash,phase=phase,attempted_cases=len(saved["cases"]),
        successful_cases=sum(r["status"]=="ok" for r in saved["cases"].values()),
        input_tokens=sum(u["input_tokens"] for u in usages), output_tokens=sum(u["output_tokens"] for u in usages),
        cached_input_tokens=sum(u.get("input_tokens_details",{}).get("cached_tokens",0) for u in usages),
        estimated_cost_usd=sum(cost(u) for u in usages),
        elapsed_seconds=sum(r["elapsed_seconds"] for r in saved["cases"].values()),
        missing_usage_calls=sum(not r.get("usage") for r in saved["cases"].values()),
        billing_note="API-reported tokens priced at frozen official rates; estimate, not invoice")
    if phase=="pilot" and summary["successful_cases"]==5:
        n=sum(c["phase"]=="evaluation" for c in inputs.values())
        summary.update(evaluation_cases=n,projected_evaluation_input_tokens=summary["input_tokens"]*n/5,
            projected_evaluation_output_tokens=summary["output_tokens"]*n/5,
            projected_evaluation_cost_usd=summary["estimated_cost_usd"]*n/5,
            projected_evaluation_seconds=summary["elapsed_seconds"]*n/5,
            projection_note="Linear projection from five development cases; evaluation sizes and cache behavior may differ")
    write(output/(phase+"-usage.json"),summary)
    print(json.dumps(summary),flush=True)
    report(output)


def score(predictions, labels, inputs):
    ids=[k for k,c in inputs.items() if c["phase"]=="evaluation"]
    valid={k:predictions[k] for k in ids if k in predictions and predictions[k].get("status","ok")=="ok"}
    raw=[k for k in ids if labels[k]["kind"]=="untouched"]
    by_kind={}
    for kind in KINDS:
        keys=[k for k in ids if labels[k]["kind"]==kind]
        measured=[k for k in keys if k in valid]
        detected=classified=0
        for k in measured:
            targets=set(labels[k]["intervention"]["observed_target_indexes"])
            matching=[a for a in valid[k]["alarms"] if targets.intersection(a["indexes"])]
            detected+=bool(matching)
            classified+=any(a["kind"]==kind for a in matching)
        complete=len(measured)==len(keys)
        by_kind[kind]=dict(planned=len(keys),measured=len(measured),detected=detected,correct_type=classified,
            detection_rate=detected/len(keys) if complete and keys else None,
            type_identification_rate=classified/len(keys) if complete and keys else None)
    latencies=[p["elapsed_seconds"] for p in valid.values()]
    raw_valid=[k for k in raw if k in valid]
    return dict(planned_cases=len(ids),successful_cases=len(valid),failed_cases=sum(k in predictions and predictions[k].get("status","ok")!="ok" for k in ids),
        by_kind=by_kind,untouched=dict(planned_windows=len(raw),measured_windows=len(raw_valid),
            alarm_windows=sum(bool(valid[k]["alarms"]) for k in raw_valid),
            alarms=sum(len(valid[k]["alarms"]) for k in raw_valid)),
        alarm_kind_counts=dict(collections.Counter(a["kind"] for p in valid.values() for a in p["alarms"])),
        latency_seconds=dict(total=sum(latencies),median=statistics.median(latencies) if latencies else None,
                             max=max(latencies) if latencies else None),
        input_tokens=sum(p.get("usage",{}).get("input_tokens",0) for p in valid.values()),
        output_tokens=sum(p.get("usage",{}).get("output_tokens",0) for p in valid.values()))


def report(output):
    verify(output)
    labels, inputs = read(output/"labels.json"), read(output/"inputs.json")
    result=dict(status="CONVENTIONAL_ONLY_AI_PENDING", generated_utc=now(), methods={},
        limitations=read(output/"protocol.json")["limitations"], natural_fault_ground_truth_available=False,
        claim="Synthetic integrity sensitivity only. No AI superiority, natural-fault recall or false-positive rate inferred.")
    if (output/"conventional.json").exists():
        for name, method in read(output/"conventional.json")["methods"].items():
            result["methods"][name]=score(method["cases"],labels,inputs)
            scan=method["untouched_full_half_scan"]
            result["methods"][name]["untouched_full_half_scan"]=dict(windows=len(scan),
                alarm_windows=sum(bool(p["alarms"]) for p in scan.values()),alarms=sum(len(p["alarms"]) for p in scan.values()),
                frames=sum(len(b["records"]) for b in read(output/"untouched-scan-inputs.json").values()),
                seconds=sum(p["elapsed_seconds"] for p in scan.values()))
    if (output/"ai-evaluation.json").exists():
        ai=read(output/"ai-evaluation.json")["cases"]
        result["methods"]["openai"]=score(ai,labels,inputs)
        result["status"]="COMPLETE" if result["methods"]["openai"]["successful_cases"]==60 else "AI_PARTIAL"
    else:
        result["methods"]["openai"]={"status":"NOT_MEASURED", "detection_rate":None,"input_tokens":None,"output_tokens":None}
    write(output/"metrics.json",result)
    lines=["# RARiS synthetic integrity benchmark", "", "Status: "+result["status"], "",
        "The three public files reproduce the archived hashes and 8,470 STF records. Structural integrity is not detector fault truth.","",
        "Evaluation: 48 labelled interventions (12 each kind), paired with 12 untouched windows. Detectors receive only observed records and first-half source references. Protocol, implementation, inputs and labels were hashed before evaluation.","",
        "| Method | Missing detected / typed | Duplicate detected / typed | Reorder detected / typed | Header detected / typed | Untouched alarm windows / alarms | Seconds (60 selected cases) | Input / output tokens |", 
        "|---|---|---|---|---|---|---|---|"]
    for name,m in result["methods"].items():
        if "by_kind" not in m:
            lines.append(f"| {name} | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |")
            continue
        cells=[f'{m["by_kind"][k]["detected"]}/{m["by_kind"][k]["planned"]} / {m["by_kind"][k]["correct_type"]}/{m["by_kind"][k]["planned"]}' for k in KINDS]
        lines.append("| "+" | ".join([name]+cells+[f'{m["untouched"]["alarm_windows"]}/{m["untouched"]["measured_windows"]} / {m["untouched"]["alarms"]}',f'{m["latency_seconds"]["total"]:.6f}', f'{m["input_tokens"]} / {m["output_tokens"]}'])+" |")
    lines += ["", "Counts credit only alarms overlapping the known intervention target; correct type additionally requires the injected type. Failure/missing API cases are explicitly listed in metrics.json and rates remain null for incomplete classes.", "",
              "Untouched alarms are natural anomaly candidates, not proven false positives. The conventional full-second-half scan has different coverage from the selected API comparison; see metrics.json.","",
              "Times measure detector function calls or synchronous API latency, excluding preparation and scoring. They do not measure real-time DAQ throughput. Token use is API-reported; conventional methods use zero API tokens.","",
              "## Limitations",""] + ["- "+x for x in result["limitations"]]
    if (output/"pilot-usage.json").exists():
        pilot=read(output/"pilot-usage.json")
        lines += ["", "## Pilot usage", "", "```json", json.dumps(pilot,indent=2), "```"]
    if (output/"evaluation-usage.json").exists():
        lines += ["", "## Evaluation usage", "", "```json", json.dumps(read(output/"evaluation-usage.json"),indent=2), "```"]
    (output/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("download","prepare","conventional","pilot","evaluate","report"))
    parser.add_argument("--data",type=Path,default=Path(".local/raris"))
    parser.add_argument("--output",type=Path,default=ROOT/"results"/"quantitative-v1")
    parser.add_argument("--budget-usd",type=float,default=1.0)
    args=parser.parse_args()
    try:
        if args.command=="download": download(args.data)
        elif args.command=="prepare": prepare(args.data,args.output)
        elif args.command=="conventional": measure_conventional(args.output)
        elif args.command=="pilot": run_api(args.output,"pilot",args.budget_usd)
        elif args.command=="evaluate": run_api(args.output,"evaluation",args.budget_usd)
        else: report(args.output)
    except (ValueError,FileNotFoundError) as error:
        # Only our own fixed messages; never print generic network exception bodies.
        if isinstance(error,FileNotFoundError): print("Required artifact is missing; run preparation/pilot first",file=sys.stderr)
        else: print(str(error),file=sys.stderr)
        return 1
    except Exception:
        print("Unexpected error; sensitive exception details suppressed",file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
