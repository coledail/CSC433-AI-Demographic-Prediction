# Running the code

Run these commands from the main project folder. Use Python 3.10 or newer.
The experiment scripts use Python's built-in libraries. You don't need to install
anything to read or score the finished experiment.

## Check the code

```sh
python3 -m unittest discover -s tests -v
```

## Score the saved answers again

This reads existing responses and makes a local copy of the scores. It makes no
model requests and costs nothing.

```sh
mkdir -p runs
cp -R results/details runs/review
python3 -m scripts.run_free_experiments runs/review
```

Look in `runs/review/` for `comparison_results.json` and `summary.json`.
Files in `runs/` stay on your computer and aren't uploaded to GitHub.

## Collect model answers

Only do this if you want to collect or finish a run. Keep Google and Groq on their
free plans with billing disabled. The runner uses a free OpenRouter model and
checks its price before starting. Free quotas can cause pauses or stop a run.

Put your own keys in a local `.env` file:

```text
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
OPENROUTER_API_KEY=your_key
```

That file is ignored by Git. Never put a real key in these instructions.

```sh
python3 -m scripts.run_free_experiments runs/review --collect
```

Existing responses are kept, so this skips samples already collected. To make a
separate new trial, copy the prompts and labels into a new folder and leave out
old responses. Don't run two collectors on the same folder at once.

For slow Google responses, add `--google-workers 3`. Each worker gets different
samples. If a daily quota runs out, wait for it to reset and use the same command.

## Prepare a new set of comments

Download `synthpai.jsonl` from [SynthPAI](https://huggingface.co/datasets/RobinSta/SynthPAI).
Keep the large source file outside the repository, then run:

```sh
python3 -m scripts.experiments prepare /path/to/synthpai.jsonl runs/new_experiment --profiles 15 --counts 1 3 5 --seed 433
```

This saves the prompts and correct answers separately. Only prompts go to models.
The same person's first comment is included in their three-comment sample, and
those three are included in their five-comment sample.

## Update the shared results

After checking your local responses, this copies the saved free-pilot results into
`results/` and rebuilds its overview. It makes no model requests.

```sh
python3 -m scripts.publish_free_results
```

It reads `runs/free_pilot/`, the local folder used for the completed study. For a
fresh checkout, copy `results/details/` there first. Keep a separate folder for any
new trial so it doesn't overwrite the completed study.

## Cole's original preparation script

```sh
python3 -m scripts.main
```

This script needs `pandas` and Hugging Face access through `fsspec` and `huggingface_hub`.
It saves the original prompt files in `data/original/`. The grouped experiment above
is the version used for the finished model comparison.

## Run the evaluation

Run these commands from the main project folder.

```sh
python3 evaluations/evaluate.py
```

To generate the graphs, install Matplotlib and run:

```sh
python3 -m pip install matplotlib
python3 evaluations/visualize.py
```

The evaluation produces:

- `evaluations/outputs/` - Evaluation results in CSV format.
- `evaluations/figures/` - Graphs in PNG and PDF formats.

No API keys are required to evaluate the saved predictions or generate the graphs.

