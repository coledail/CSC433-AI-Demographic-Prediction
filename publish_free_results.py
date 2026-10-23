"""Export reviewable empirical artifacts for evaluation; never copies credentials."""
import json
from pathlib import Path
import shutil
from collections import Counter
from datetime import datetime, timezone
from run_free_experiments import MODELS, export
from experiments import read_jsonl


def publish(source=Path('runs/free_pilot'), destination=Path('results/free_pilot')):
    labels=read_jsonl(source/'labels.jsonl')
    export(source, labels)
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('requests.jsonl','labels.jsonl','manifest.json','responses.jsonl',
                 'summary.json','comparison_results.json'):
        shutil.copyfile(source/name,destination/name)
    # Failed/invalid outputs remain auditable; omit account/provider error payloads.
    invalid=[]
    for name in MODELS:
        p=source/f'{name}.jsonl'
        if p.exists():
            invalid += [r for r in read_jsonl(p) if r['status']!='ok']
    (destination/'invalid_responses.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in invalid))
    errors=[]
    for path in sorted(source.glob('*_errors.jsonl')):
        rows=read_jsonl(path)
        errors.append({'model_alias':path.stem.removesuffix('_errors'),
                       'error_count':len(rows),
                       'http_status_counts':dict(Counter(str(r.get('http_status',r.get('error_type'))) for r in rows))})
    (destination/'collection_errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    if (source/'collector_events.jsonl').exists():
        shutil.copyfile(source/'collector_events.jsonl',destination/'collector_events.jsonl')
    if (source/'excluded_duplicates.jsonl').exists():
        shutil.copyfile(source/'excluded_duplicates.jsonl',destination/'excluded_duplicates.jsonl')
    responses=read_jsonl(source/'responses.jsonl')
    comparisons=json.loads((source/'comparison_results.json').read_text())
    summary=json.loads((source/'summary.json').read_text())
    manifest=json.loads((source/'manifest.json').read_text())
    manifest['collection_status']=comparisons['status']
    manifest['exported_at']=datetime.now(timezone.utc).isoformat()
    manifest['validated_responses_by_model']={name:sum(r['model']==name for r in responses) for name in MODELS}
    manifest['observed_openrouter_cost_usd']=sum(r.get('usage',{}).get('cost',0) or 0 for r in responses if r.get('provider')=='openrouter')
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    profiles={row['profile_id']:row['actual_attributes'] for row in labels}
    baselines={attribute:{'most_common_label':counts.most_common(1)[0][0], 'count':counts.most_common(1)[0][1], 'n':len(profiles)} for attribute in ('age_group','gender','location') if (counts:=Counter(row[attribute] for row in profiles.values()))}
    (destination/'label_distribution_reference.json').write_text(json.dumps(baselines,indent=2)+'\n')
    table=['| Model | Valid responses | Expected |','|---|---:|---:|']
    for alias,(_,model,_) in MODELS.items():
        n=sum(r['model']==alias for r in responses)
        table.append(f'| {model} | {n} | {len(labels)} |')
    scores=['| Model | Comments | Age-group accuracy | Gender accuracy | Exact location accuracy |',
            '|---|---:|---:|---:|---:|']
    for alias,(_,model,_) in MODELS.items():
        for count in (1,3,5):
            cells=[]
            for attr in ('age_group','gender','location'):
                row=next((r for r in summary if r['model']==alias and r['comment_count']==count and r['attribute']==attr),None)
                cells.append(f"{row['accuracy']:.1%} ({row['n']}/{row['expected']} valid)" if row else 'Pending')
            scores.append(f'| {model} | {count} | '+ ' | '.join(cells)+' |')
    report='''# LLM inference handoff for Tabiya

## Collection status

STATUS: **STATUS_VALUE**. These are real API responses, not generated example results.

MODEL_TABLE

## Accuracy among valid responses

SCORE_TABLE

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
'''
    report=report.replace('STATUS_VALUE',comparisons['status'].upper()).replace('MODEL_TABLE','\n'.join(table)).replace('SCORE_TABLE','\n'.join(scores))
    (destination/'HANDOFF.md').write_text(report)
    # A final scan catches inadvertent credential content without printing it.
    secrets=[line.split('=',1)[1] for line in Path('.env').read_text().splitlines() if '=' in line]
    for path in destination.iterdir():
        content=path.read_text()
        if any(secret and secret in content for secret in secrets):
            raise ValueError(f'Credential detected in {path.name}; refusing publication')
    print(f'Prepared {destination}: {len(responses)} validated responses')


if __name__=='__main__':
    publish()
