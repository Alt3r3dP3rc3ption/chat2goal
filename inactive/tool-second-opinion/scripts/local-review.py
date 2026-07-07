#!/usr/bin/env python3
"""Local private review via Ollama API — explicit num_ctx + artifact-fit check.

Proč ne `ollama run`: CLI nedrží explicitní num_ctx a Ollama pak dlouhý artefakt
TIŠE ořízne — model sebejistě "zrevievuje" i text, který nečetl (nález z
cross-vendor review 2026-07-05). API volání s explicitním num_ctx + fit-check
tomu zabrání. Thinking modely (qwen3.6) vrací v "response" jen finální odpověď.

Usage: local-review.py <model_tag> <prompt_file> [num_ctx=16384]
Exit:  0 OK (review na stdout) · 3 FIT-FAIL (artefakt se nevejde do kontextu)
"""
import json, sys, time, urllib.request, pathlib

model = sys.argv[1]
path = pathlib.Path(sys.argv[2])
num_ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 16384

prompt = path.read_text(encoding="utf-8")
est = int(len(prompt.split()) * 1.8)  # hrubý odhad tokenů pro CZ/EN mix
if est > num_ctx - 512:
    sys.stderr.write(
        f"FIT-FAIL: ~{est} tok > num_ctx {num_ctx}. Artefakt se nevejde — zkrať ho, "
        f"shrň sekce, nebo zvyš num_ctx (pozor na RAM: KV cache roste s kontextem).\n")
    sys.exit(3)

body = json.dumps({
    "model": model, "prompt": prompt, "stream": False, "keep_alive": "3m",
    "options": {"num_ctx": num_ctx, "temperature": 0.2},
}).encode()
req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                             headers={"Content-Type": "application/json"})
t0 = time.time()
data = json.loads(urllib.request.urlopen(req, timeout=1800).read())
sys.stderr.write(f"[{model} | {time.time()-t0:.0f}s | prompt_tok={data.get('prompt_eval_count')} "
                 f"out_tok={data.get('eval_count')}]\n")
print(data.get("response", ""))
