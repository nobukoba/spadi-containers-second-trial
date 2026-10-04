#!/usr/bin/env python3
"""Inspect NestDAQ v1 STF files; no anomaly truth or AI accuracy is inferred."""
import argparse
import hashlib
import json
import statistics
import struct
from pathlib import Path

FS_MAGIC = 0x004B4E53454C4946
STF_MAGIC = 0x00454D4954425553
HEADER = struct.Struct("<QIHHIIIIQQ")

def inspect(path):
    data = path.read_bytes()
    if len(data) < 304 or struct.unpack_from("<Q", data)[0] != FS_MAGIC:
        raise ValueError(f"{path}: unsupported FileSink header")
    offset = struct.unpack_from("<H", data, 12)[0]
    if offset < 304 or offset > len(data):
        raise ValueError(f"{path}: invalid FileSink header length")
    frames = []
    while offset < len(data):
        if data[offset:offset+8] == b"FILETRL\x00":
            if len(data)-offset != 304 or struct.unpack_from("<IH", data, offset+8) != (304, 304):
                raise ValueError(f"{path}: invalid FileSink trailer")
            break
        if offset + HEADER.size > len(data):
            raise ValueError(f"{path}: truncated STF header at {offset}")
        magic, length, hlen, kind, tfid, femtype, femid, messages, sec, usec = HEADER.unpack_from(data, offset)
        if magic != STF_MAGIC or hlen != 48 or length < hlen or offset + length > len(data):
            raise ValueError(f"{path}: invalid STF at {offset}")
        frames.append(dict(source=path.parent.name, offset=offset, length=length,
                           timeframe_id=tfid, fem_type=femtype, fem_id=femid,
                           messages=messages, time_sec=sec, time_usec=usec,
                           raw_header_hex=data[offset:offset+48].hex()))
        offset += length
    return dict(file=str(path), sha256=hashlib.sha256(data).hexdigest(),
                bytes=len(data), trailing_bytes=len(data)-offset), frames

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.data.glob("*/run000020.dat"))
    if not paths:
        parser.error("no */run000020.dat files")
    args.output.mkdir(parents=True, exist_ok=True)
    sources, all_frames, flags = [], [], []
    for path in paths:
        source, frames = inspect(path)
        sizes = [f["length"] for f in frames]
        if not sizes:
            raise ValueError(f"{path}: no frames")
        # A descriptive byte-volume screen, NOT a detector-event-rate metric.
        # First half establishes a threshold; only second half is screened.
        cut = len(sizes)//2
        if not cut:
            raise ValueError("at least two frames required")
        threshold = 3 * statistics.median(sizes[:cut])
        selected = [f for f in frames[cut:] if f["length"] > threshold]
        sources.append(dict(**source, frames=len(frames), development_frames=cut,
                            screen_frames=len(frames)-cut, median_bytes=statistics.median(sizes),
                            max_bytes=max(sizes), threshold_bytes=threshold,
                            byte_volume_flags=len(selected)))
        all_frames.extend(frames)
        flags.extend(selected)
    with (args.output/"frames.jsonl").open("w") as f:
        for frame in all_frames:
            f.write(json.dumps(frame)+"\n")
    summary = dict(status="DATA_INSPECTION_ONLY", sources=sources,
                   total_frames=len(all_frames), flagged_frames=len(flags),
                   ground_truth_available=False, ai_evaluated=False,
                   limitations=["Frame byte volume is not event rate.",
                                "Flags are candidates, not confirmed anomalies.",
                                "All files are from the same run; no independent held-out run.",
                                "No precision, recall or false-alarm rate can be computed.",
                                "No full streaming, container or API execution measured."])
    (args.output/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    (args.output/"candidate-windows.json").write_text(json.dumps(flags[:10], indent=2)+"\n")
    examples = sorted(all_frames, key=lambda f: f["length"], reverse=True)[:5]
    (args.output/"unlabelled-examples.json").write_text(json.dumps(examples, indent=2)+"\n")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
