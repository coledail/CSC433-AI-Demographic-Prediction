# Results

The experiment is **COMPLETE**. We collected real predictions from four free
models using 15 made-up people from SynthPAI. Each model saw 1, 3 and 5 comments
from each person, for 180 responses in total.

## Start here

- [Predictions beside the correct answers](comparison_results.json)
- [Accuracy and confidence numbers](summary.json)
- [Original responses, prompts and experiment settings](details/)
- [How we ran the experiment and things to keep in mind](../docs/experiment_notes.md)

Tabiya can use the comparison file to make tables and graphs. A `null` prediction
means the model chose not to answer. Those answers count as incorrect in accuracy.

## How often each model was correct

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

Each complete row covers 15 people. Location means getting both the city and
country right. Different spellings can count as wrong, so review those before
drawing conclusions. Confidence is how sure the model says it is; it can still be wrong.

Nine of the 15 people have a male label. Always guessing male would score 60%,
which helps put the gender results in context. This is a small study using synthetic
profiles, so it does not show that the models can identify real people.
