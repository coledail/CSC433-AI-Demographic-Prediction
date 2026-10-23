# LLM inference handoff for Tabiya

## Collection status

STATUS: **COMPLETE**. These are real API responses, not generated example results.

| Model | Valid responses | Expected |
|---|---:|---:|
| gemini-3.5-flash-lite | 45 | 45 |
| openai/gpt-oss-20b | 45 | 45 |
| qwen/qwen3.8-27b | 45 | 45 |
| nvidia/nemotron-3.5-lightning:free | 45 | 45 |

## Accuracy among valid responses

| Model | Comments | Age-group accuracy | Gender accuracy | Exact location accuracy |
|---|---:|---:|---:|---:|
| gemini-3.5-flash-lite | 1 | 0.0% (15/15 valid) | 0.0% (15/15 valid) | 0.0% (15/15 valid) |
| gemini-3.5-flash-lite | 3 | 20.0% (15/15 valid) | 0.0% (15/15 valid) | 13.3% (15/15 valid) |
| gemini-3.5-flash-lite | 5 | 46.7% (15/15 valid) | 13.3% (15/15 valid) | 20.0% (15/15 valid) |
| openai/gpt-oss-20b | 1 | 46.7% (15/15 valid) | 53.3% (15/15 valid) | 6.7% (15/15 valid) |
| openai/gpt-oss-20b | 3 | 40.0% (15/15 valid) | 66.7% (15/15 valid) | 13.3% (15/15 valid) |
| openai/gpt-oss-20b | 5 | 33.3% (15/15 valid) | 53.3% (15/15 valid) | 13.3% (15/15 valid) |
| qwen/qwen3.8-27b | 1 | 40.0% (15/15 valid) | 26.7% (15/15 valid) | 6.7% (15/15 valid) |
| qwen/qwen3.8-27b | 3 | 40.0% (15/15 valid) | 53.3% (15/15 valid) | 6.7% (15/15 valid) |
| qwen/qwen3.8-27b | 5 | 46.7% (15/15 valid) | 80.0% (15/15 valid) | 6.7% (15/15 valid) |
| nvidia/nemotron-3.5-lightning:free | 1 | 46.7% (15/15 valid) | 60.0% (15/15 valid) | 6.7% (15/15 valid) |
| nvidia/nemotron-3.5-lightning:free | 3 | 33.3% (15/15 valid) | 60.0% (15/15 valid) | 6.7% (15/15 valid) |
| nvidia/nemotron-3.5-lightning:free | 5 | 26.7% (15/15 valid) | 60.0% (15/15 valid) | 6.7% (15/15 valid) |

## Files

- `comparison_results.json`: actual attributes, predictions, confidence and correctness per sample/model.
- `responses.jsonl`: validated real responses, raw model text, exact returned identifiers, settings and token usage.
- `invalid_responses.jsonl`: raw responses that failed schema validation; never silently repaired.
- `labels.jsonl`: withheld ground truth and source comment IDs.
- `requests.jsonl`: exact prompts sent to models, without ground-truth profile fields.
- `summary.json`: per-model/condition/attribute accuracy, coverage and confidence reliability bins.
- `manifest.json`: dataset checksum, seed, model IDs, cohort and methodology changes.
- `collection_errors.json`: sanitized error counts; full error payloads stay local.

## Method and limits

15 synthetic SynthPAI profiles, with 1, 3 and 5 nested comments per profile. Profiles
are the first 15 of the original seeded pilot; they were chosen before seeing any
predictions. The original commercial lineup was replaced to meet a $0 budget.
Models and providers are distinct concepts. GPT-OSS is hosted by Groq and is not
the ChatGPT product.
No inference is performed on real people. Each request uses a fresh context with no
tools. Labels are joined only after model responses are received.

Accuracy denominators in the table are VALID responses, not expected responses.
A fully collected condition has 15 valid responses. Pending and invalid predictions
remain visible in the comparison JSON. Do not treat incomplete cells as comparable
population estimates. For comparisons across models or text amounts, use the same
profiles with valid predictions in every compared condition and report that N.
Abstentions count as incorrect in accuracy; confidence summaries exclude abstentions.
Model-reported confidence is not a calibrated probability. The cohort contains
9 male labels out of 15: a constant male prediction scores 60% on gender. Treat
that as a descriptive label-distribution reference, not a trained or held-out
baseline. `label_distribution_reference.json` supplies the corresponding counts. Location scoring is strict
city/country equality after case/whitespace normalization; aliases can lower accuracy.
Gender uses the dataset's male/female labels. Age is evaluated in fixed bins.

Gemma endpoints failed before producing any predictions; retired Gemini 2.5 endpoints
rejected new users. The original Nemotron endpoint returned a provider 404, so an
explicitly free Nemotron 3.5 Lightning endpoint was selected before collecting its
first prediction. Gemini 3.8 timed out before returning a prediction and was replaced with GPT-OSS
20B on Groq. No model was selected or retried based on correctness. Retry logs
include rate limits and transient server failures. The user confirmed Google billing
is disabled; requests use free plans and OpenRouter's explicitly zero-priced variant.
Groq rejected some requests because their maximum output allowance exceeded the
free output-token quota; subsequent requests use a 512-token cap instead of 2048.
Per-response settings preserve this change. Completed outputs were retained; no
response was retried because of correctness. One collector restart overlapped a
Qwen request; the first response was retained and the duplicate is preserved in
`excluded_duplicates.jsonl`, outside the scoring denominator.
Google's remaining samples were assigned to three disjoint worker partitions to
reduce free-tier latency. A pending request may have been in flight at restart;
no returned prediction was discarded. Completed checkpoints were retained.
No payment details were entered and no billing upgrades were performed.

## Suggested evaluation work

Compare accuracy by attribute and text amount on a shared complete cohort. Review
location spelling mismatches; report any alias normalization rule separately. Plot
confidence versus correctness with sample counts and note sparse calibration bins.
Group by actual location/gender/age where sample sizes permit; avoid conclusions
from tiny groups. Synthetic data and a small cohort cannot establish real-world
privacy risk, causal effects or broad demographic disparities. No train/test split
or fine-tuning is used. More comments can also add misleading information, so an
accuracy increase is not assumed.
