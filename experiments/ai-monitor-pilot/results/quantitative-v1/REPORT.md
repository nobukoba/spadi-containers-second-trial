# RARiS synthetic integrity benchmark

Status: AI_PARTIAL

The three public files reproduce the archived hashes and 8,470 STF records. Structural integrity is not detector fault truth.

Evaluation: 48 labelled interventions (12 each kind), paired with 12 untouched windows. Detectors receive only observed records and first-half source references. Protocol, implementation, inputs and labels were hashed before evaluation.

| Method | Missing detected / typed | Duplicate detected / typed | Reorder detected / typed | Header detected / typed | Untouched alarm windows / alarms | Seconds (60 selected cases) | Input / output tokens |
|---|---|---|---|---|---|---|---|
| byte_volume | 0/12 / 0/12 | 0/12 / 0/12 | 0/12 / 0/12 | 0/12 / 0/12 | 0/12 / 0 | 0.000191 | 0 / 0 |
| structural_rules | 12/12 / 12/12 | 12/12 / 12/12 | 12/12 / 12/12 | 12/12 / 12/12 | 0/12 / 0 | 0.001461 | 0 / 0 |
| openai | 2/12 / 2/12 | 9/12 / 9/12 | 11/12 / 10/12 | 8/12 / 7/12 | 3/5 / 4 | 64.989513 | 221663 / 5108 |

Counts credit only alarms overlapping the known intervention target; correct type additionally requires the injected type. Failure/missing API cases are explicitly listed in metrics.json and rates remain null for incomplete classes.

Untouched alarms are natural anomaly candidates, not proven false positives. The conventional full-second-half scan has different coverage from the selected API comparison; see metrics.json.

Times measure detector function calls or synchronous API latency, excluding preparation and scoring. They do not measure real-time DAQ throughput. Token use is API-reported; conventional methods use zero API tokens.

## Limitations

- Same-run halves, not an independent held-out run
- No natural fault truth or detector burst data
- Four synthetic header variants only
- Paired cases share base windows; counts are not independent samples
- No cross-source alignment claim
- No real-time DAQ throughput measurement
- No baseline results or injection labels supplied to AI

## Pilot usage

```json
{
  "freeze_sha256": "421f356f17bfbcef4a3c42ce0b93cc113cb0e45568c45fc015333a6c4e32e105",
  "phase": "pilot",
  "attempted_cases": 5,
  "successful_cases": 5,
  "input_tokens": 28630,
  "output_tokens": 937,
  "cached_input_tokens": 0,
  "estimated_cost_usd": 0.012951200000000001,
  "elapsed_seconds": 16.542447499959962,
  "missing_usage_calls": 0,
  "billing_note": "API-reported tokens priced at frozen official rates; estimate, not invoice",
  "evaluation_cases": 60,
  "projected_evaluation_input_tokens": 343560.0,
  "projected_evaluation_output_tokens": 11244.0,
  "projected_evaluation_cost_usd": 0.1554144,
  "projected_evaluation_seconds": 198.50936999951955,
  "projection_note": "Linear projection from five development cases; evaluation sizes and cache behavior may differ"
}
```

## Evaluation usage

```json
{
  "freeze_sha256": "421f356f17bfbcef4a3c42ce0b93cc113cb0e45568c45fc015333a6c4e32e105",
  "phase": "evaluation",
  "attempted_cases": 60,
  "successful_cases": 39,
  "input_tokens": 340014,
  "output_tokens": 9918,
  "cached_input_tokens": 6784,
  "estimated_cost_usd": 0.1498392,
  "elapsed_seconds": 111.63116509999963,
  "missing_usage_calls": 0,
  "billing_note": "API-reported tokens priced at frozen official rates; estimate, not invoice"
}
```
