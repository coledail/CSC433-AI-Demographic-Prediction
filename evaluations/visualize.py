"""Generate slide/report figures from evaluated CSV; requires matplotlib."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
NAMES = {"gemini35_flash_lite": "Gemini", "gpt_oss20b": "GPT-OSS", "qwen3_8_27b": "Qwen", "nemotron3_super": "Nemotron"}
ATTR = ["age_group", "gender", "location"]
LABELS = {"age_group": "Age group", "gender": "Gender", "location": "Exact location"}


def save(fig, name):
    target = HERE / "figures"
    target.mkdir(exist_ok=True)
    fig.savefig(target / (name + ".png"), dpi=220, bbox_inches="tight")
    fig.savefig(target / (name + ".pdf"), bbox_inches="tight")
    plt.close(fig)


def main():
    path = HERE / "outputs" / "evaluation_summary.csv"
    if not path.exists():
        raise SystemExit("First run: python evaluations/evaluate.py")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    data = {(r["model"], int(r["comment_count"]), r["attribute"]): r for r in rows}
    models = list(NAMES)
    # 5-comment model comparison. Rates are % over all profiles, including null answers.
    fig, ax = plt.subplots(figsize=(9, 4.7))
    offsets = (-0.25, 0, 0.25)
    for i, attribute in enumerate(ATTR):
        values = [100*float(data[(m, 5, attribute)]["accuracy"]) for m in models]
        ax.bar([j+offsets[i] for j in range(len(models))], values, width=0.24, label=LABELS[attribute])
    ax.set_xticks(range(len(models)), [NAMES[m] for m in models])
    ax.set_ylim(0, 100); ax.set_ylabel("Accuracy (% of all 15 profiles)")
    ax.set_title("Demographic prediction accuracy with five comments")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
    ax.grid(axis="y", alpha=0.2); ax.set_axisbelow(True)
    save(fig, "model_accuracy")

    # Facets avoided; one figure with independent lines grouped by attribute, generated separately.
    for attribute in ATTR:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for model in models:
            values = [100*float(data[(model, n, attribute)]["accuracy"]) for n in (1, 3, 5)]
            ax.plot([1, 3, 5], values, marker="o", label=NAMES[model], linewidth=2)
        ax.set_xticks([1, 3, 5]); ax.set_ylim(0, 100)
        ax.set_xlabel("Comments supplied per synthetic profile")
        ax.set_ylabel("Accuracy (% of all 15 profiles)")
        ax.set_title(f"Effect of comment count on {LABELS[attribute].lower()} prediction")
        ax.legend(ncol=2, frameon=False); ax.grid(alpha=0.2)
        save(fig, f"comments_{attribute}")

    fig, ax = plt.subplots(figsize=(9, 4.7))
    for i, attribute in enumerate(ATTR):
        values = [100*float(data[(m, 5, attribute)]["coverage"]) for m in models]
        ax.bar([j+offsets[i] for j in range(len(models))], values, width=0.24, label=LABELS[attribute])
    ax.set_xticks(range(len(models)), [NAMES[m] for m in models])
    ax.set_ylim(0, 100); ax.set_ylabel("Coverage (% answering)")
    ax.set_title("How often did models provide a prediction? (five comments)")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
    ax.grid(axis="y", alpha=0.2); ax.set_axisbelow(True)
    save(fig, "coverage")
    print("Saved figures as PNG (slides) and vector PDF (LaTeX).")


if __name__ == "__main__":
    main()
