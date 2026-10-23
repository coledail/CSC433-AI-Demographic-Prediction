# AI Demographic Prediction

Can an AI guess someone's age group, gender or location from their writing?
That's what we're testing for CSC 433.

We used comments from 15 made-up people in the SynthPAI dataset. Four free models
read 1, 3 and 5 comments from each person. We saved their guesses and how confident
they were, then checked those guesses against the dataset's answers.

**All 180 model responses are collected.** Tabiya can now use them for the evaluation,
graphs and privacy discussion.

## Where to look

| Folder | What's inside |
|---|---|
| [results/](results/) | The finished comparison file and a readable results overview. Start here. |
| [scripts/](scripts/) | Python code that prepares the comments, runs the models and saves results. |
| [data/original/](data/original/) | Cole's original prepared prompts and answers. |
| [docs/](docs/) | Notes on how the experiment worked and how to run the code. |
| [tests/](tests/) | Checks that the code groups comments and scores answers correctly. |

## What we found

The models gave different answers. Qwen did better on gender when it had more
comments. Exact location was harder, and more text didn't help every model.
Gemini often chose not to answer.

We used Gemini Flash-Lite, GPT-OSS, Qwen and Nemotron to keep the project free.
These replace the originally planned ChatGPT, Claude and DeepSeek comparison.
The exact model names are saved with the results.

This is a small experiment with synthetic profiles. It shows what happened in our
sample; it doesn't prove that AI can identify real people.

## Team

- **Cole:** dataset preparation and related research.
- **David:** model testing, predictions, text-length comparisons and confidence scores.
- **Tabiya:** evaluation, tables, graphs and privacy analysis.

No API keys are included in the repository. You don't need keys to read or analyze
the saved results. See [the running instructions](docs/running_the_code.md) if you
want to repeat the experiment.
