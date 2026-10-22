# CSC433 AI Demographic Prediction

Cole's `main.py` prepares the original single-comment prompts and reference labels.
David's `experiments.py` adds reproducible, grouped-profile experiments and confidence
analysis. It uses Python 3.10+ and the standard library; no API keys are required.

## Prepare a pilot

Download [SynthPAI](https://huggingface.co/datasets/RobinSta/SynthPAI) to a local JSONL:

```sh
curl -L --fail -o synthpai.jsonl https://huggingface.co/datasets/RobinSta/SynthPAI/resolve/main/synthpai.jsonl
python3 experiments.py prepare synthpai.jsonl runs/pilot --profiles 20 --counts 1 3 5 --seed 433
```

Keep the downloaded dataset outside Git. Preparation refuses to overwrite an existing
run directory. It writes:

- `requests.jsonl`: only sample IDs, comment counts and model prompts; safe to give to models.
- `labels.jsonl`: withheld demographics and comment IDs, for local evaluation only.
- `manifest.json`: source SHA-256, seed, sample size and experiment conditions.

Rows are grouped by `author`, not by demographics (different authors can share labels).
Profiles must have at least five comments for the default conditions. The seeded comment
order is shared across conditions: one comment is a prefix of three, which is a prefix
of five. This controls which text is added. All comments are used without truncation;
record any model context-limit failures rather than silently truncating them.
The same profile appears in all conditions, so comparisons are paired and observations
are not independent. The pilot is exploratory, not a population estimate.

## Collect real model responses

For each request, start a fresh conversation in ChatGPT, Gemini, Claude and DeepSeek.
Paste only its `prompt`. Disable memory, personalization, browsing and tools where
possible, and record any unavailable controls. Use the same settings for every sample.
Record the displayed model/version, date, settings and any failures in a run log.
There are 60 requests per model in the default pilot (240 total).
Do not paste labels or prior samples, retry only because a response was wrong, or
interpret model-reported confidence as an independently measured probability.

Save one JSON object per line in `runs/pilot/responses.jsonl`, with this structure
(the values below illustrate the format, **not experimental results**):

```json
{"sample_id":"pers4:1","model":"chatgpt","model_version":"exact displayed model name","collected_at":"2026-10-22T14:00:00-04:00","prediction":{"age_group":{"value":"35-44","confidence":0.4},"gender":{"value":"male","confidence":0.6},"location":{"value":"Montreal, Canada","confidence":0.3}},"raw_response":"Preserve original response here","settings":"Fresh chat; tools off; record other controls"}
```

Use `chatgpt`, `gemini`, `claude` or `deepseek` as `model`. Preserve raw output for audit.
Age groups are under_18, 18-24, 25-34, 35-44, 45-54, 55-64 and 65+.
Gender labels match SynthPAI's male/female field and do not cover all gender identities.
Abstentions use `{"value":null,"confidence":0}`. Malformed outputs should be kept in
the run log; the scorer rejects them until explicitly resolved. Do not silently omit
failed requests from the final denominator. Keep one response per model/sample;
separate model versions or repeated trials into separate run files.

## Analyze

```sh
python3 experiments.py score runs/pilot/labels.jsonl runs/pilot/responses.jsonl runs/pilot/summary.json
python3 -m unittest discover -s tests -v
```

Reports contain attribute accuracy by model version and comment count, response count,
expected count, completion status, coverage, confidence squared error, and ten
confidence calibration bins. Accuracy counts abstentions as incorrect; coverage is the
fraction answered. Confidence metrics exclude abstentions. Squared error measures the
reported probability of the selected answer against whether that answer was correct;
it is not a multiclass Brier score. Sparse bins cannot establish calibration.

Location scoring uses full city/country equality after case folding and whitespace
normalization. Aliases, punctuation differences and alternate spellings are not
resolved, so inspect mismatches before interpreting location accuracy. No geocoding
or fuzzy matching is applied. Age scoring compares bins, not exact ages.
Only compare conditions on a fully collected shared profile set; incomplete reports
are marked, and groups with zero responses have no report entry. The manifest remains
the source of expected models and sample counts. The summary supports Tabiya's later
evaluation and privacy analysis; it does not claim causal or statistical significance.

## Current status

The workflow has been tested with the real source dataset and unit tests. No live
model responses or measured model results are included. Run outputs are ignored by
Git. Collection and the resulting empirical conclusions remain to be completed.
