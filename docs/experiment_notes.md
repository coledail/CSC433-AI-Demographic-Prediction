# Experiment Notes

## Dataset and Samples

We used 15 synthetic profiles from the SynthPAI dataset. Profiles were
selected using a fixed seed of 433. Each profile had samples of 1, 3,
and 5 comments.

Four models received the same 45 samples, producing 180 responses.
The correct demographic labels were hidden from the models.

## Models

| Model | API Provider |
|---|---|
| Gemini 3.5 Flash-Lite | Google |
| GPT-OSS 20B | Groq |
| Qwen 3.8 27B | Groq |
| Nemotron 3.5 Lightning | OpenRouter |

We used these models to stay within free API limits.

## Experiment Settings

- Temperature: 0
- Fresh conversation for each request
- No browsing or external tools
- Confidence scores between 0 and 1
- Null values allowed for unanswered predictions
- Output limit: 2048 tokens, reduced to 512 for later Groq requests

## Evaluation

Predictions were compared against the known demographic labels.
We ignored capitalization and extra spaces. Location required an
exact city and country match.

We measured accuracy, coverage, answered-only accuracy, and
confidence error. We also used the most common label for each
attribute as a baseline.

Unanswered predictions counted as incorrect for overall accuracy.

## Collection Issues

Some API requests failed due to service errors and free usage limits.
One duplicate Qwen response was excluded, and the first response
was kept regardless of correctness.

## Limitations

The experiment used only 15 synthetic profiles and four models.
The results may not represent real users. Confidence scores were
self-reported and may not be reliable.

## Results

- [Experiment settings](../results/details/manifest.json)
- [Saved predictions](../results/comparison_results.json)
- [Evaluation results](../evaluations/)
