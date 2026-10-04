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

## Quantitative synthetic integrity trial

A host-only Windows Python implementation is now provided in `benchmark.py`.
See `RUNBOOK.md` for commands and API-key handling, and
`results/quantitative-v1/REPORT.md` for measured outputs. The original descriptive
inspection files above remain separate from the new benchmark.

The three fixed-revision public files were fetched again and matched all prior
SHA-256 hashes, sizes and the total of 8,470 STF records. All adjacent IDs advance
by four; no timestamp regression or invalid microsecond field was found. This is
structural evidence, not a statement that detector data is fault-free.

The first half of each source supplies reference values. Five development cases
are used for API usage/cost measurement. Evaluation uses four non-overlapping
second-half windows per source, each with an untouched variant and four synthetic
variants: missing, duplicate, adjacent swap and malformed header. There are 60
selected evaluation cases, including 48 interventions and 12 untouched controls.
Protocol, exact prompt/model, implementation, inputs and labels were hash-frozen
before conventional evaluation or API pilot execution. Detectors receive the same
observed headers, decoded fields, physical lengths and payload hashes. Neither
receives intervention locations, original offsets, labels, or the other's output.

The conventional byte-volume screen is retained as the historical baseline; an
additional structural-rule baseline prevents crediting the AI for anomalies that
simple sequence/header checks already resolve. Both also scan all 4,236
second-half untouched records (133 windows). The AI's untouched scan covers only
the selected 12 windows. Do not compare their different broader coverage as if it
were the same sample, or label untouched alerts as proven false positives.

Synthetic detection and type identification require an alarm at the injected
location. Record boundaries are preserved, so header corruption is tested as a
framed-record inspection problem; byte-stream resynchronization is unmeasured.
This same-run, paired-window experiment does not establish independent-run
performance, natural-fault recall, actual detector bursts or DAQ streaming speed.
AWS application Submit remains outside the performed work.

The Windows API run attempted all 60 evaluation cases once: 39 valid outputs and
21 rejected outputs. Accepted localized synthetic detections were 30/48, with
28/48 also matching the injected type. In contrast, structural rules detected and
typed 48/48; the byte-volume screen detected 0/48. No AI superiority was shown.
Only five of twelve untouched API windows had valid outputs: three had four
candidate alarms, and seven remain indeterminate. The rejected response bodies
were not retained, limiting retrospective failure diagnosis. Usage for all 65
pilot/evaluation requests was 368,644 input and 10,855 output tokens, with estimated
cost USD 0.1627904. See `RESULTS-ja.md`, `outcome-summary.json` and the per-case
records for coverage, timing scopes, failure treatment and interpretation.
