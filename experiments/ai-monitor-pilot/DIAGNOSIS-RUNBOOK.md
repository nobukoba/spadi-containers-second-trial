# Contextual diagnosis pilot (synthetic)

The model calls are not yet executed. This experiment tests interpretation of
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
