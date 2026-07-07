# Reviewer tiers, setup & dependencies

Reference for `tool-second-opinion`. SKILL.md holds the workflow; this holds the setup detail,
verified invocations, dependency matrix, and roadmap.

## The three tiers

| Tier | Reviewer | Location | Jurisdiction | Role |
|------|----------|----------|--------------|------|
| Baseline | `claude` headless | cloud (Anthropic) | US / GDPR-safe | sanity anchor for NON-sensitive work |
| Cloud cross-vendor | `gemini --skip-trust -m gemini-3.5-flash` | cloud (Google) | US (EU-US DPF) | vendor-diversity signal for NON-sensitive work |
| Local private | `ollama run "$QWEN_TAG"` | LOCAL (your machine — reference: Apple Silicon 32GB) | nothing leaves the machine | the ONLY reviewer for sensitive work; offline fallback |

## Detection notes (verified 2026-06-27 on an Apple Silicon 32GB machine — do not re-discover)

- **Gemini CLI** is `@google/gemini-cli`, auto-reads `GEMINI_API_KEY` from env. Headless invocation
  **requires `--skip-trust`** (or `GEMINI_CLI_TRUST_WORKSPACE=true`) — a bare `gemini -p` errors with
  "not running in a trusted directory". Model `gemini-3.5-flash` confirmed valid (verified 2026-07-05,
  A/B-tested against 2.5-pro on a real review — Flash gave the sharper, more concrete output).
  `gemini-2.5-pro` is DEPRECATED (2026-06-17, EOL 2026-10-17) — do not revert to it. `gemini-3.5-pro`
  has NO public API ID (not GA). Alt if Flash misbehaves: `gemini-3.1-pro-preview` (works, preview tier).
- **Local model** tag this machine: `qwen3.6:27b` (Ollama 0.30.x, 17 GB, dense, thinking model,
  256K ctx — but on 32 GB use num_ctx 16384). Chosen 2026-07-05 via seeded-defect gate: recall 22/22,
  čeština ~4.9/5, 0-1 halucinace, ~5–8 min/review (thinking). Alternatives installed: `gemma4:26b`
  (21/22, ~1 min, fast manual local pass) — NOT in routing per cross-vendor consensus (KISS).
  Retired: `qwen3-coder:30b` (19/22, nejvíc halucinací — špatná čísla řádků, spekulace). Always use
  the captured `$QWEN_TAG` from detection, never a hardcoded tag — `ollama list` is the source of truth.
- **Ollama bind** — if `OLLAMA_HOST` is `0.0.0.0:*`, the "local" tier is reachable from the LAN. Treat
  as non-private until rebound to `127.0.0.1`.
- **Verified live:** `gemini --skip-trust -m gemini-3.5-flash -p` → OK; `ollama run qwen3-coder:30b` → OK.

## Vision tier (added 2026-07-05)

`scripts/vision-review.py` — image QA routing on top of the same trust zones. Measured baseline
(4 tasks, ground truth ze zdrojáků, seeded defect; detail v `context/learnings.md`
§ tool-second-opinion):

| Backend | Defect recall | False positives | Speed/task | Role |
|---------|--------------|-----------------|------------|------|
| `gemini-3.5-flash` (vision) | 3/3 | 0 | 7–13 s | default cloud eyes (NON-sensitive only) |
| `gemma4:26b` (vision, local) | 2/3 | 0 | ~25–45 s | default LOCAL eyes + fallback |
| `qwen3.6:27b` (vision, local) | 2/3 | 0 | ~3,5 min | `--route deep` — thorough/sensitive |
| Claude subagents via Read | 1/3 | 0 | ~15 s | not routed — orchestrator, not eyes |

Detection: skript čte Ollama `/api/tags` + `/api/show` a bere jen modely s capability `vision` —
žádné hardcoded tagy. Pasti gemini CLI @-příloh (tichá záměna souboru mimo cwd; `.env` auth vyžaduje
spouštění z rootu repa) řeší skript a dokumentuje SKILL.md. **Edge-checklist prompt** (projdi všechny
4 okraje) zvedl recall z 1/3 na 3/3 — stejná lekce jako checklist probes u textu: scaffolding je
větší páka než výběr modelu. Vision routing gemma4 POUŽÍVÁ (rychlost); text-review routing zůstává
qwen-only (KISS rozhodnutí výše).

## Dependencies

| Tool | Required? | What it provides | Without it |
|------|-----------|------------------|------------|
| `claude` CLI | Required | Baseline review (always available here) | Skill cannot run |
| `gemini` CLI (`@google/gemini-cli`) + `GEMINI_API_KEY` | Optional, recommended | Cloud cross-vendor signal + vision QA cloud eyes | Degrades; install hint once: `npm install -g @google/gemini-cli` |
| `ollama` + a `qwen*` model | Optional, recommended | Local private tier — the ONLY reviewer allowed for sensitive work | Sensitive work blocks until installed; non-sensitive proceeds on Claude ± Gemini |
| `ollama` + a vision model (`gemma4*`/`qwen3.6*`) | Optional | Local private VISION tier (citlivé obrázky) | Sensitive image QA blocks; non-sensitive uses Gemini |
| `scripts/classify-sensitivity.sh` | Bundled | Layer-1 hard privacy scan (regex, TEXT only — obrázky klasifikuje člověk per Step 1.5) | No automated gate; rely on human judgement only — weaker |
| `scripts/vision-review.py` | Bundled | Vision QA router (qa / fit / describe; PASS/FAIL exit protokol) | No image QA tier |

## Excluded (by decision)

- **Codex / OpenAI tier** — excluded 2026-06-27 (cost; user decision). Revisit only if free-tier OpenAI
  access changes or a review demands gpt-tier reasoning Gemini + Qwen can't match.

## Roadmap

- ✅ **Auto-classify privacy gate** — DONE 2026-06-27. `scripts/classify-sensitivity.sh` hard-blocks
  cloud routing on regex hits (secrets, conn strings, internal IP/host, `clients/`, contact dumps,
  confidential markers). Fails toward local. Tuning lives in that script.
- ✅ **Bigger / general local model** — DONE 2026-07-05. `qwen3.6:27b` replaced `qwen3-coder:30b`
  after a seeded-defect test gate (8 artefaktů, 22 defektů: recall 100 % vs 86 %, méně halucinací,
  lepší čeština). `gemma4:26b` installed as fast manual alternative. Srpen 2026: revisit OpenEuroLLM
  (EU projekt, první plné modely 31. 7.) jako kandidáta na CZ-validovaný tier.
- **Classifier tuning** — extend `classify-sensitivity.sh` patterns as new sensitive shapes appear
  (e.g. new internal hostnames, new secret prefixes). Keep it failing-toward-local.
