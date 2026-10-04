#!/usr/bin/env python3
"""Synthetic contextual diagnosis, not validated natural-fault causality."""
import argparse
import copy
import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
import benchmark as base

ROOT = Path(__file__).resolve().parent
CAUSES = ["configured_selection", "queue_drop", "connection_interruption", "unknown"]
PROMPT = """Assess the observed ID discontinuity using only the supplied record fields
and optional synthetic configuration/log observations. Return a candidate, not a claim of
verified physical causation. An ID step may be deliberate selection, queue discards,
connection interruption, or unexplained. Do not infer absence of a cause from absent logs.
Conflicting supporting evidence should yield unknown rather than a unique cause.
Evidence references must be IDs of supplied observations. Checks are non-destructive:
inspect_selection_config, inspect_queue_counters, inspect_connection_history,
collect_missing_context. Give one or more useful checks. No truth labels are supplied.
Output only the required JSON."""
CHECKS = ["inspect_selection_config", "inspect_queue_counters",
          "inspect_connection_history", "collect_missing_context"]
SCHEMA = {"type":"object","additionalProperties":False,
 "properties":{"candidate":{"type":"string","enum":CAUSES},
 "evidence_ids":{"type":"array","items":{"type":"string"}},
 "checks":{"type":"array","items":{"type":"string","enum":CHECKS}}},
 "required":["candidate","evidence_ids","checks"]}

def write(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")

def context_rules(blind):
    context = blind["context"]
    selected, dropped, disconnected = [], [], []
    for e in context:
        if e.get("component") == "output" and e.get("selection_stride") == 8:
            selected.append(e["id"])
        if e.get("component") == "output" and e.get("discarded_delta", 0) > 0 and e.get("queue_fraction", 0) >= .95:
            dropped.append(e["id"])
        if e.get("component") == "output" and e.get("event") == "disconnected":
            disconnected.append(e["id"])
    choices = [(CAUSES[0],selected,CHECKS[0]), (CAUSES[1],dropped,CHECKS[1]),
               (CAUSES[2],disconnected,CHECKS[2])]
    supported = [x for x in choices if x[1]]
    if len(supported) != 1:
        return dict(candidate="unknown", evidence_ids=sum([x[1] for x in supported], []),
                    checks=[CHECKS[3]])
    cause, ids, check = supported[0]
    return dict(candidate=cause, evidence_ids=ids, checks=[check])

def prepare(out):
    if out.exists():
        raise ValueError("Output already exists; choose a new directory")
    with zipfile.ZipFile(ROOT/"results/quantitative-v1/frozen-inputs.zip") as z:
        old = json.loads(z.read("inputs.json"))
    labels = json.loads((ROOT/"results/quantitative-v1/labels.json").read_text())
    windows = [(k,c) for k,c in old.items() if labels[k]["kind"]=="untouched"]
    dev = [c for k,c in windows if c["phase"]=="development"]
    evaluation = [c for k,c in windows if c["phase"]=="evaluation"]
    if not dev or len(evaluation)!=12:
        raise ValueError("Unexpected source selection")
    cases, truth = {}, {}
    rng = random.Random(20261005)
    # All observed data in this experiment is derived; no real configuration/log
    # observation or actual fault cause is asserted.
    for phase, groups in [("pilot",dev[:1]),("evaluation",evaluation[:8])]:
        for wi,c in enumerate(groups):
            source = c["input"]["records"]
            ids = [r["timeframe_id"] for r in source[::2]]
            variants = ["selection","queue","connection","absent","conflict"]
            for scenario in variants:
                events = [
                    dict(component="other_monitor",event="disconnected"),
                    dict(component="output",queue_fraction=.20,discarded_delta=0)]
                positive=[]
                if scenario in ("selection","conflict"):
                    positive.append(dict(component="output",selection_stride=8))
                if scenario in ("queue","conflict"):
                    positive.append(dict(component="output",queue_fraction=.99,discarded_delta=16))
                if scenario=="connection":
                    positive.append(dict(component="output",event="disconnected"))
                events += positive
                rng.shuffle(events)
                for i,e in enumerate(events):
                    e["id"]="E"+str(i)
                blind = dict(data=dict(observed_timeframe_ids=ids,reference_id_step=4),
                             context=events, provenance="synthetic_context_and_selected_record_ids")
                candidate = {"selection":CAUSES[0],"queue":CAUSES[1],"connection":CAUSES[2]}.get(scenario,"unknown")
                required = CHECKS[CAUSES.index(candidate)]
                key = hashlib.sha256((phase+str(wi)+scenario).encode()).hexdigest()[:16]
                cases[key]=dict(phase=phase,input=blind)
                evidence=[e["id"] for e in events if e in positive]
                truth[key]=dict(candidate=candidate, required_check=required,
                               supported_evidence_ids=evidence,scenario=scenario,
                               paired_group=phase+str(wi))
    protocol=dict(model=base.MODEL,prompt=PROMPT,schema=SCHEMA,max_output_tokens=600,
                  limitations=["Synthetic configuration and logs, no natural cause truth.",
                   "Same-run paired windows, not independent faults.",
                   "Scenario construction favors explicit evidence matching; not a broad reasoning test.",
                   "Expert check usefulness requires separate blinded human assessment."],
                  source_commit="c5a78f93bed24ad0de67ec2c2e9875e7a95f8d17",
                  prices= dict(input=.4,cached_input=.1,output=1.6))
    out.mkdir(parents=True)
    write(out/"inputs.json",cases);write(out/"labels.json",truth);write(out/"protocol.json",protocol)
    write(out/"freeze.json",{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
       for p in [out/"inputs.json",out/"labels.json",out/"protocol.json",Path(__file__),ROOT/"benchmark.py"]})
    conventional = {k:dict(structure_only=dict(candidate="unknown",evidence_ids=[],checks=[CHECKS[3]]),
                           context_rules=context_rules(c["input"])) for k,c in cases.items()}
    write(out/"conventional.json",conventional)
    report(out)
    print("Prepared: five development cases, 40 evaluation cases; two AI conditions")

def verify(out):
    for name,h in json.loads((out/"freeze.json").read_text()).items():
        path = out/name if name.endswith(".json") else ROOT/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=h:
            raise ValueError("Frozen artifact changed")

def validate(pred, blind):
    if set(pred)!={"candidate","evidence_ids","checks"} or pred["candidate"] not in CAUSES:
        raise ValueError("Invalid output")
    if not isinstance(pred["evidence_ids"],list) or not isinstance(pred["checks"],list):
        raise ValueError("Invalid output")
    ids={e["id"] for e in blind["context"]}
    if any(not isinstance(x,str) or x not in ids for x in pred["evidence_ids"]):
        raise ValueError("Invalid evidence reference")
    if not pred["checks"] or any(x not in CHECKS for x in pred["checks"]):
        raise ValueError("Invalid check")

def api(blind, protocol):
    key=os.environ["OPENAI_API_KEY"]
    body=dict(model=protocol["model"],instructions=protocol["prompt"],input=json.dumps(blind),
        temperature=0,store=False,max_output_tokens=protocol["max_output_tokens"],
        text={"format":dict(type="json_schema",name="diagnosis",strict=True,schema=protocol["schema"])})
    request=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(body).encode(),
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    start=time.perf_counter()
    try:
        with urllib.request.urlopen(request,timeout=60) as response:
            result=json.load(response)
    except urllib.error.HTTPError as e:
        return dict(status="http_error",http_status=e.code,usage=None,seconds=time.perf_counter()-start)
    except (urllib.error.URLError,TimeoutError,OSError):
        return dict(status="transport_error",usage=None,seconds=time.perf_counter()-start)
    # Retain completed/incomplete response bodies for failure diagnosis, but never
    # retain headers, credentials or HTTP error bodies.
    sanitized=json.dumps(result).replace(key,"[REDACTED]")
    result=json.loads(sanitized)
    saved=dict(status="invalid_output",raw_response=result,usage=result.get("usage"),
               seconds=time.perf_counter()-start)
    try:
        if result.get("status")!="completed":
            saved["status"]="incomplete"
            return saved
        text="".join(x["text"] for item in result["output"] for x in item.get("content",[])
                     if x.get("type")=="output_text")
        pred=json.loads(text);validate(pred,blind)
        saved.update(status="ok",prediction=pred)
    except (ValueError,KeyError,TypeError):
        pass
    return saved

def run(out, phase, budget):
    verify(out)
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not set; no request sent")
    cases=json.loads((out/"inputs.json").read_text())
    protocol=json.loads((out/"protocol.json").read_text())
    target=out/("ai-"+phase+".json")
    saved=json.loads(target.read_text()) if target.exists() else {}
    if any(r.get("usage") is None for r in saved.values()):
        raise ValueError("Prior usage unknown; review before sending further requests")
    spent=sum(base.cost(r["usage"]) for r in saved.values())
    for k,c in cases.items():
        if c["phase"]!=phase:continue
        for condition in ["data_only","with_context"]:
            rid=k+":"+condition
            if rid in saved:continue
            blind=copy.deepcopy(c["input"])
            if condition=="data_only":blind["context"]=[]
            # One-byte-per-token reserve plus prompt/schema allowance and max output.
            reserve=(len(json.dumps(blind).encode())+len(PROMPT.encode())+4000)*.4/1e6+600*1.6/1e6
            if spent+reserve>budget:
                write(out/"usage-"+phase+".json",dict(estimated_cost_usd=spent,status="budget_stop"))
                print("Budget reserve reached; no additional request sent");return
            r=api(blind,protocol);saved[rid]=r;write(target,saved)
            if r.get("usage") is None:
                print("Usage unknown; stopped without retry");return
            spent+=base.cost(r["usage"])
            if r["status"]!="ok":
                print("Response failure retained; stopped without retry");report(out);return
    write(out/("usage-"+phase+".json"),dict(calls=len(saved),
       input_tokens=sum(r["usage"]["input_tokens"] for r in saved.values()),
       output_tokens=sum(r["usage"]["output_tokens"] for r in saved.values()),
       seconds=sum(r["seconds"] for r in saved.values()),estimated_cost_usd=spent,
       evaluation_cost_projection=spent*8 if phase=="pilot" else None,
       invoice=False))
    report(out)

def report(out):
    verify(out)
    truth=json.loads((out/"labels.json").read_text());cases=json.loads((out/"inputs.json").read_text())
    conv=json.loads((out/"conventional.json").read_text())
    ai=json.loads((out/"ai-evaluation.json").read_text()) if (out/"ai-evaluation.json").exists() else {}
    methods={}
    for method in ["structure_only","context_rules","data_only","with_context"]:
        total=valid=correct=checks=unsupported=unknown_correct=unknown_total=0
        for k,c in cases.items():
            if c["phase"]!="evaluation":continue
            total+=1;t=truth[k]
            if t["candidate"]=="unknown":unknown_total+=1
            if method in ["structure_only","context_rules"]:pred=conv[k][method]
            else:
                r=ai.get(k+":"+method,{})
                if r.get("status")!="ok":continue
                pred=r["prediction"]
            valid+=1;correct+=pred["candidate"]==t["candidate"]
            checks+=t["required_check"] in pred["checks"]
            unsupported+=len(set(pred["evidence_ids"])-set(t["supported_evidence_ids"]))
            unknown_correct+=t["candidate"]=="unknown" and pred["candidate"]=="unknown"
        methods[method]=dict(planned=total,valid=valid,candidate_matches=correct,
            operational_match_fraction=correct/total if valid or any(k+":"+method in ai for k,c in cases.items() if c["phase"]=="evaluation") else None,
            required_check_matches=checks,unsupported_evidence_references=unsupported,
            unknown_correct=unknown_correct,unknown_planned=unknown_total,
            expert_usefulness="NOT_EVALUATED")
    write(out/"metrics.json",dict(status="AI_PENDING" if not ai else "AI_PARTIAL_OR_COMPLETE",
       methods=methods,claim="Synthetic evidence interpretation only; no demonstrated natural-fault diagnosis."))
    print(json.dumps(methods,indent=2))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["prepare","pilot","evaluate","report"])
    p.add_argument("--output",type=Path,default=ROOT/"results/diagnosis-v1")
    p.add_argument("--budget-usd",type=float,default=.10)
    a=p.parse_args()
    if not 0<a.budget_usd<=1:raise ValueError("Budget must be >0 and <=1 USD per phase")
    if a.command=="prepare":prepare(a.output)
    elif a.command=="report":report(a.output)
    else:run(a.output,"pilot" if a.command=="pilot" else "evaluation",a.budget_usd)
if __name__=="__main__":
    try:main()
    except ValueError as e:print(str(e));raise SystemExit(1)
