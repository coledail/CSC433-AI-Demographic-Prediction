"""Recompute evaluation metrics from saved model predictions (stdlib only).

Run at repository root: python evaluations/evaluate.py
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
ATTRIBUTES = ("age_group", "gender", "location")


def normalize(value):
    return " ".join(value.casefold().split()) if isinstance(value, str) else None


def write_csv(path, records, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def analyze():
    source = json.loads((RESULTS / "comparison_results.json").read_text(encoding="utf-8"))
    profiles = {r["profile_id"]: r["actual_attributes"] for r in source["comparisons"]}
    if len(profiles) != source["profile_count"]:
        raise ValueError("Unexpected number of profiles")
    if len(source["comparisons"]) != source["sample_count"]:
        raise ValueError("Unexpected number of samples")
    labels = {attribute: Counter(p[attribute] for p in profiles.values()) for attribute in ATTRIBUTES}
    baselines = {a: {"label": c.most_common(1)[0][0], "correct": c.most_common(1)[0][1], "n": len(profiles)} for a, c in labels.items()}
    samples = defaultdict(list)
    details = []
    location_review = []
    for item in source["comparisons"]:
        for model, output in item["ai_results"].items():
            if output["status"] != "ok":
                raise ValueError(f"Missing/invalid model output for {item['sample_id']} {model}")
            for attribute in ATTRIBUTES:
                actual = item["actual_attributes"][attribute]
                predicted = output["predicted_attributes"][attribute]
                answered = predicted is not None
                correct = int(answered and normalize(predicted) == normalize(actual))
                confidence = output["confidence"][attribute]
                if answered and (not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1):
                    raise ValueError(f"Invalid confidence for {item['sample_id']} {model} {attribute}")
                previously = output["matches_actual"][attribute]
                if previously is not None and bool(previously) != bool(correct):
                    raise ValueError(f"Stored match differs for {item['sample_id']} {model} {attribute}")
                row = {"profile_id": item["profile_id"], "sample_id": item["sample_id"],
                       "model": model, "comment_count": item["comment_count"], "attribute": attribute,
                       "actual": actual, "predicted": predicted or "", "answered": int(answered),
                       "correct": correct, "confidence": confidence if answered else ""}
                details.append(row)
                samples[(model, item["comment_count"], attribute)].append(row)
                if attribute == "location" and answered and not correct:
                    location_review.append(row.copy())
    summary = []
    for (model, count, attribute), entries in sorted(samples.items()):
        n = len(entries)
        answered = [r for r in entries if r["answered"]]
        correct = sum(r["correct"] for r in entries)
        brier = sum((r["confidence"] - r["correct"])**2 for r in answered) / len(answered) if answered else None
        summary.append({"model": model, "comment_count": count, "attribute": attribute,
                        "n": n, "answered": len(answered), "correct": correct,
                        "accuracy": correct/n, "coverage": len(answered)/n,
                        "answered_accuracy": correct/len(answered) if answered else None,
                        "confidence_mse": brier, "baseline_label": baselines[attribute]["label"],
                        "baseline_accuracy": baselines[attribute]["correct"]/baselines[attribute]["n"]})
    official = {(r["model"], r["comment_count"], r["attribute"]): r for r in json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))}
    for row in summary:
        key = row["model"], row["comment_count"], row["attribute"]
        if key not in official:
            raise ValueError(f"Missing summary combination {key}")
        for metric in ("accuracy", "coverage", "confidence_mse"):
            expected, observed = official[key][metric], row[metric]
            if (expected is None) != (observed is None) or (expected is not None and abs(expected-observed)>1e-10):
                raise ValueError(f"Validation failed for {key} {metric}: {expected} versus {observed}")
    if len(official) != len(summary):
        raise ValueError("Extra combinations found in existing summary")
    outputs = HERE / "outputs"
    write_csv(outputs / "evaluation_summary.csv", summary,
              ["model", "comment_count", "attribute", "n", "answered", "correct", "accuracy", "coverage", "answered_accuracy", "confidence_mse", "baseline_label", "baseline_accuracy"])
    write_csv(outputs / "prediction_details.csv", details,
              ["profile_id", "sample_id", "model", "comment_count", "attribute", "actual", "predicted", "answered", "correct", "confidence"])
    write_csv(outputs / "location_review.csv", location_review,
              ["profile_id", "sample_id", "model", "comment_count", "attribute", "actual", "predicted", "answered", "correct", "confidence"])
    return summary, len(profiles), len(details)


if __name__ == "__main__":
    summary, profiles, total = analyze()
    print(f"Validated {len(summary)} metric combinations, {total} attribute outcomes, {profiles} profiles.")
    print("Wrote evaluations/outputs/ (including location mismatches for manual review).")
