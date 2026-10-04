# RARiS AI monitoring pilot

This host-side preparation uses the same public run000020.dat files listed in
scripts/nestdaq/raris-ac-lgad/config.sh. It requires Python 3 with no packages.
It does not require rebuilding a container.

From the repository root, with downloaded files below the persistent workspace:

```bash
python3 experiments/ai-monitor-pilot/prepare.py \
  /workspace/spadi/rawdata/raris_ac_lgad_202603 \
  --output /workspace/spadi/ai-monitor-pilot
```

Supported format: FileSink v1 and SubTimeFrame v1, checked against
spadi-alliance/nestdaq-user-impl revision 47897e9bdc4dac2f429909b3fa8bf05ab93115d0.
The raw data source revision used for this initial inspection is
nobukoba/container-interfacing-nestdaq-eicrecon ccf94e725389b5d32b2cd167312deb88c6461eba.

Outputs include file hashes, frame offsets, header bytes, unlabelled large-frame
examples and a descriptive byte-volume screen. Files are inspected independently;
the three source streams are not asserted to align or form complete TimeFrames.
The threshold is three times the first-half median; only the second half is screened.
This is not detector event rate, anomaly truth or an independent held-out run.

Initial execution: 8,470 STF records across three source files, with zero second-half
byte-volume flags. This cannot establish that the data is fault-free. No AI calls,
precision/recall, false-alarm rate or streaming throughput were measured.
The execution environment had neither Docker/Apptainer nor API credentials.

Next: identify expert-confirmed fault and comparison intervals, preferably from
separate runs. Freeze interval selection, prompts and thresholds before evaluation.
Use identical intervals for conventional baseline, AI without context, and AI with
logs/configuration. Store exact prompts, model/version, outputs, request latency and
API token usage. Label synthetic interventions separately from naturally occurring
faults; never report duplicated bytes as a verified detector burst. Do not publish
API credentials, private logs or experimental data without permission.
