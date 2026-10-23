"""Run a fixed free-model pilot, checkpoint every response, and export comparisons."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
import threading
import urllib.error
import urllib.request

from scripts.experiments import read_jsonl, validate_prediction, score, norm

# Google and Groq require Free-plan accounts with billing disabled.
# OpenRouter is restricted to an explicitly zero-priced :free model, no fallback.
WRITE_LOCK = threading.Lock()

MODELS = {
    'gemini35_flash_lite': ('google', 'gemini-3.5-flash-lite', 12),
    'gpt_oss20b': ('groq', 'openai/gpt-oss-20b', 8),
    'qwen3_8_27b': ('groq', 'qwen/qwen3.8-27b', 8),
    'nemotron3_super': ('openrouter', 'nvidia/nemotron-3.5-lightning:free', 5),
}


def request_json(url, key, payload=None, google=False):
    headers = {'User-Agent': 'CSC433-Research/1.0', 'Content-Type': 'application/json'}
    headers.update({'x-goog-api-key': key} if google else {'Authorization': 'Bearer ' + key})
    request = urllib.request.Request(url, headers=headers,
                                     data=json.dumps(payload).encode() if payload is not None else None)
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def parse_prediction(text):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text).strip()
    return validate_prediction(json.loads(text))


def append(path, row):
    with WRITE_LOCK, path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        stream.flush()


def run_model(name, requests, directory, keys):
    provider, model, delay = MODELS[name]
    path = directory / f'{name}.jsonl'
    existing = read_jsonl(path) if path.exists() else []
    if not path.exists() and (directory/'responses.jsonl').exists():
        existing = [r for r in read_jsonl(directory/'responses.jsonl') if r['model']==name]
        for row in existing:
            append(path, row)
    done = {r['sample_id'] for r in existing}
    for request in requests:
        if request['sample_id'] in done:
            continue
        result = {'sample_id': request['sample_id'], 'model': name,
                  'model_version': model, 'provider': provider,
                  'collected_at': datetime.now(timezone.utc).isoformat(),
                  'settings': {'temperature': 0, 'max_output_tokens': 2048,
                               'fresh_context': True, 'tools': False}}
        for attempt in range(3):
            try:
                if provider == 'google':
                    # User confirmed Google Free tier with billing disabled before collection.
                    data = request_json(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                                        keys['GEMINI_API_KEY'],
                                        {'contents': [{'role':'user','parts':[{'text':request['prompt']}]}],
                                         'generationConfig': {'temperature':0,'maxOutputTokens':2048}}, google=True)
                    candidate = data.get('candidates', [{}])[0]
                    raw = ''.join(p.get('text','') for p in candidate.get('content',{}).get('parts',[]) if not p.get('thought'))
                    result['finish_reason'] = candidate.get('finishReason')
                    result['settings']['thinking'] = 'provider default'
                    result['returned_model'] = data.get('modelVersion', model)
                else:
                    endpoint = 'https://api.groq.com/openai/v1/chat/completions' if provider == 'groq' else 'https://openrouter.ai/api/v1/chat/completions'
                    payload = {'model':model, 'messages':[{'role':'user','content':request['prompt']}],
                               'temperature':0, 'max_tokens':512 if provider=='groq' else 2048}
                    result['settings']['max_output_tokens'] = payload['max_tokens']
                    if provider == 'openrouter':
                        payload['provider'] = {'allow_fallbacks':False, 'max_price':{'prompt':0,'completion':0}}
                        payload['reasoning'] = {'enabled':False}
                    else:
                        payload['reasoning_effort'] = 'low' if model.startswith('openai/gpt-oss') else 'none'
                        result['settings']['reasoning_effort'] = payload['reasoning_effort']
                        payload['response_format'] = {'type':'json_object'}
                    data = request_json(endpoint, keys['GROQ_API_KEY' if provider=='groq' else 'OPENROUTER_API_KEY'], payload)
                    raw = data['choices'][0]['message'].get('content') or ''
                    result['finish_reason'] = data['choices'][0].get('finish_reason')
                    result['returned_model'] = data.get('model', model)
                result['raw_response'] = raw
                result['usage'] = data.get('usageMetadata', data.get('usage',{}))
                try:
                    result['prediction'] = parse_prediction(raw)
                    result['status'] = 'ok'
                except (ValueError, TypeError) as error:
                    result['status'] = 'invalid_output'
                    result['error'] = str(error)
                append(path, result)
                print(f'{name} {request["sample_id"]} {result["status"]}', flush=True)
                break
            except urllib.error.HTTPError as error:
                # Never log headers, URLs containing keys, or credentials.
                message = error.read().decode(errors='replace')
                for secret in keys.values():
                    if secret:
                        message = message.replace(secret, '[REDACTED]')
                append(directory / f'{name}_errors.jsonl',
                       {'sample_id':request['sample_id'],'http_status':error.code,
                        'attempt':attempt+1,'error':message[:3000],
                        'at':datetime.now(timezone.utc).isoformat()})
                print(f'{name} HTTP {error.code} attempt {attempt+1}', flush=True)
                if error.code in (429, 500, 502, 503, 504) and attempt < 2:
                    # Stop immediately on daily quota; minute throttles get bounded backoff.
                    if any(token in message.lower() for token in ('perday', 'per_day', 'daily', 'limit: 0')):
                        return
                    time.sleep(min(float(error.headers.get('Retry-After', 30)), 60))
                    continue
                return
            except (TimeoutError, OSError) as error:
                append(directory/f'{name}_errors.jsonl', {'sample_id':request['sample_id'],
                       'error_type':type(error).__name__,'at':datetime.now(timezone.utc).isoformat()})
                print(f'{name} network error; checkpoint saved', flush=True)
                return
        time.sleep(delay)


def export(directory, labels):
    shared = read_jsonl(directory/'responses.jsonl') if (directory/'responses.jsonl').exists() else []
    responses = [r for name in MODELS for r in (read_jsonl(directory/f'{name}.jsonl') if (directory/f'{name}.jsonl').exists() else [row for row in shared if row['model']==name])]
    valid = [r for r in responses if r['status']=='ok']
    (directory/'responses.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in valid))
    summary = score(labels, valid)
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lookup = {(r['model'],r['sample_id']):r for r in responses}
    comparison=[]
    for label in labels:
        ai={}
        for name in MODELS:
            response=lookup.get((name,label['sample_id']))
            prediction=response.get('prediction',{}) if response else {}
            ai[name]={'status':response['status'] if response else 'pending',
                      'model_version':MODELS[name][1],
                      'predicted_attributes':{a:prediction.get(a,{}).get('value') for a in label['actual_attributes']},
                      'confidence':{a:prediction.get(a,{}).get('confidence') for a in label['actual_attributes']},
                      'matches_actual':{a:(p.get('value') is not None and norm(p['value'])==norm(actual)) if (p:=prediction.get(a)) else None
                                        for a,actual in label['actual_attributes'].items()}}
        comparison.append({**label, 'ai_results':ai})
    result={'status':'complete' if len(valid)==len(labels)*len(MODELS) else 'partial',
            'profile_count':len({r['profile_id'] for r in labels}), 'sample_count':len(labels),
            'models':{name:{'provider':v[0],'model_id':v[1]} for name,v in MODELS.items()},
            'expected_predictions':len(labels)*len(MODELS), 'valid_predictions':len(valid),
            'invalid_predictions':len(responses)-len(valid),'comparisons':comparison}
    (directory/'comparison_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='comparisons'}), flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--collect',action='store_true')
    parser.add_argument('--google-workers',type=int,choices=(1,2,3),default=1)
    args=parser.parse_args()
    labels=read_jsonl(args.directory/'labels.jsonl')
    if args.collect:
        keys=dict(line.split('=',1) for line in Path('.env').read_text().splitlines() if line and not line.startswith('#'))
        # Verify OpenRouter key is free-tier and exact model has zero token prices.
        account=request_json('https://openrouter.ai/api/v1/key',keys['OPENROUTER_API_KEY'])['data']
        if not account.get('is_free_tier'):
            raise ValueError('OpenRouter account must be free-tier for this runner')
        catalog=request_json('https://openrouter.ai/api/v1/models',keys['OPENROUTER_API_KEY'])['data']
        target=next(m for m in catalog if m['id']==MODELS['nemotron3_super'][1])
        if any(float(target['pricing'][field])!=0 for field in ('prompt','completion')):
            raise ValueError('OpenRouter model no longer free; refusing to run')
        requests=read_jsonl(args.directory/'requests.jsonl')
        with ThreadPoolExecutor(max_workers=4) as pool:
            # Google models run sequentially to share the project quota politely.
            def google_models():
                for name in [n for n,v in MODELS.items() if v[0]=='google']:
                    with ThreadPoolExecutor(max_workers=args.google_workers) as google_pool:
                        parts=[requests[i::args.google_workers] for i in range(args.google_workers)]
                        jobs=[google_pool.submit(run_model,name,part,args.directory,keys) for part in parts]
                        for job in jobs:
                            job.result()
            futures=[pool.submit(google_models)]
            futures += [pool.submit(run_model,n,requests,args.directory,keys) for n,v in MODELS.items() if v[0]!='google']
            for future in futures:
                future.result()
    export(args.directory, labels)


if __name__=='__main__':
    main()
