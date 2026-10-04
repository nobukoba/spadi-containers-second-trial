# Contextual diagnosis pilot (synthetic)

The model calls were executed on 2026-10-05 (JST). See
`results/diagnosis-v1/RESULTS-ja.md` and `execution-summary.json` for all 90
attempts, failures, usage and limitations. This experiment tests interpretation of
synthetic evidence, not verified natural-fault causality. The first simple
context baseline matches all 40 synthetic cases. Matching that baseline is not
AI superiority, and a with-context improvement over data-only shows value of
information, not unique value of AI.

Five scenarios are paired with the same observed record-ID sequence:
intentional selection, queue discards, connection interruption, absent evidence,
and conflicting evidence. Unrelated-component logs act as distractors.
Record IDs come from public RARiS windows; every configuration/log is artificial.
Eight evaluation groups give 40 paired scenarios (not 40 independent faults).
The one development group is separate from evaluation data.
Inputs, labels, prompt, model, schema, runner and scorer are hash-frozen.
Do not revise after seeing evaluation results; use a new version instead.

Comparisons: structure-only abstention, context rules, AI data-only, AI context.
The structure-only reference always reports unknown; it is a diagnostic
abstention baseline, not a newly measured anomaly detector.
Score candidate match, required-check match, unsupported evidence references
and correct unknown/abstention. Required-check matching is a predefined proxy;
it is not expert judgment of usefulness. Candidate matches do not prove causes.
AI failures are saved separately and credited as unsuccessful, not valid negatives.
Unexecuted AI fractions are null.

## Windows Codex continuation

Read AGENTS.md and this document. Check out research/ai-monitor-pilot and pull.
Use the existing secure OPENAI_API_KEY process environment procedure from RUNBOOK.md.
Never paste or print credentials. No Docker or dependency installation required.

From repository root, using the checked-in frozen results:

```powershell
python -m unittest discover -s experiments/ai-monitor-pilot -p "test*.py"
python experiments/ai-monitor-pilot/diagnosis.py pilot --budget-usd 0.10
Get-Content experiments/ai-monitor-pilot/results/diagnosis-v1/usage-pilot.json
```

Pilot: five development cases, two conditions, ten calls. Inspect valid responses
and the estimated cost/projection before evaluation. Do not adjust the frozen
protocol; if pilot reveals an implementation defect, archive this version and
create a fresh version before any evaluation. If there is no usage-pilot.json,
the phase stopped early; inspect saved statuses. No auto retries occur.

Then:

```powershell
python experiments/ai-monitor-pilot/diagnosis.py evaluate --budget-usd 0.50
python experiments/ai-monitor-pilot/diagnosis.py report
Get-Content experiments/ai-monitor-pilot/results/diagnosis-v1/metrics.json
```

Evaluation: 40 cases x two conditions = 80 calls. Existing saved attempts are not
resent. Failures stop execution; repeating the same command proceeds only to
unattempted calls. Unknown prior API usage blocks further calls. Budget reserves
are conservative planning estimates, not guaranteed invoice caps. Rates are the
previous pilot's frozen gpt-4.1-mini rates; verify current official rates before
calling. The runner's model is gpt-4.1-mini-2025-04-14.
Raw successful/incomplete API response bodies are retained for diagnostics,
with defensive credential redaction; headers and HTTP error bodies are omitted.
Report API usage, failures and limitations. Review artifacts before publishing.
Do not claim AI benefit unless supported against the context-rule baseline.
Do not change the AWS application or Submit based on unmeasured results.

## Recorded execution and reruns

The recorded development phase contains ten attempts: five valid with-context
responses and five rejected data-only responses. Its reported usage was 3,765
input and 559 output tokens; estimated cost USD 0.0024004. The projected
80-call evaluation cost was USD 0.0192032, shown before evaluation.

All 80 evaluation calls were then attempted once. The data-only condition had
40 evidence-reference validation failures; with-context had 40 valid outputs,
23 candidate matches and 24 required-check matches. Context rules matched
40 candidates and 40 required checks. There was no demonstrated AI superiority.
The candidate-matching fraction is an operational score that includes interface
failures, not an isolated measure of model reasoning. Evidence IDs in this
version are restricted to context observation IDs, so data-only outputs that
reference timeframe IDs are rejected. This condition was not changed after
viewing results. All successful/incomplete/rejected model responses and known
usage were retained; no failed attempt was resent.

Calling `pilot` or `evaluate` on these saved outputs skips all existing attempts
and sends no new requests. To run the exact same frozen cases again, copy the
following existing files to a new output directory, preserving their bytes:
`inputs.json`, `labels.json`, `protocol.json`, `freeze.json`, `conventional.json`.
Do not copy `ai-*.json` or `usage-*.json` into that new directory.

```powershell
$source = 'experiments/ai-monitor-pilot/results/diagnosis-v1'
$out = '.local/diagnosis-repeat-01'
New-Item -ItemType Directory -Path $out
Copy-Item "$source/inputs.json", "$source/labels.json", "$source/protocol.json", "$source/freeze.json", "$source/conventional.json" -Destination $out
python experiments/ai-monitor-pilot/diagnosis.py pilot --output $out --budget-usd 0.10
Get-Content "$out/usage-pilot.json"
# Inspect pilot outputs and cost projection before evaluation.
python experiments/ai-monitor-pilot/diagnosis.py evaluate --output $out --budget-usd 0.50
python experiments/ai-monitor-pilot/diagnosis.py report --output $out
```

If a model output fails validation with known usage, repeating the same phase
command continues to unattempted calls only. Do not continue after unknown usage.
The original protocol/prompt/model/scorer must remain unchanged. A revised
experiment requires a new version and a fresh freeze before evaluation.

In this execution, Windows Python 3.12.14 inherited the key from the user's
PowerShell process environment through a local phase runner. The key was never
persisted in the user registry or a file. The runner was closed after execution;
remove the original shell's environment value with `Remove-Item Env:OPENAI_API_KEY`
or close that PowerShell. No Docker or AWS submission was used.
