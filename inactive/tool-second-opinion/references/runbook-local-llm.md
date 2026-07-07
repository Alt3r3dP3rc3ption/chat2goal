# Runbook — lokální LLM pro second opinion (instalace podle parametrů počítače)

Cíl: rozjet si doma dvojici lokálních modelů (Qwen = kvalitní/thinking review, Gemma =
rychlé review + vision oči) + volitelně Gemini CLI jako cloudový cross-vendor tier.
Každý počítač je jiný — tenhle runbook začíná analýzou TVÉHO stroje a teprve podle ní
doporučí velikost modelů. Referenční ověřený setup autora: Apple Silicon, 32 GB RAM,
`qwen3.6:27b` + `gemma4:26b`.

Proč zrovna Qwen + Gemma: vyhrály měřený seeded-defect test (07/2026, 8 dokumentů /
22 zasazených chyb: qwen3.6 22/22 + čeština 4,9/5; gemma4 21/22 @ ~1 min). Detaily
testu a čísla vision srovnání: `reviewer-tiers.md` v této složce.

---

## 0. Požadavky

| Nástroj | K čemu | Povinné? |
|---|---|---|
| [Ollama](https://ollama.com/download) | běh lokálních modelů | ano (pro lokální tier) |
| `python3` (3.9+) | `local-review.py`, `vision-review.py` | ano |
| `claude` CLI | baseline reviewer | už máš (Claude Code) |
| Node.js + `npm` | Gemini CLI | jen pro cloud tier |
| `gemini` CLI + `GEMINI_API_KEY` | cloud cross-vendor + rychlé vision oči | volitelné, doporučené |

---

## 1. Analýza počítače (spusť jako první)

```bash
bash scripts/setup-local-llm.sh          # jen změří a doporučí, nic nestahuje
```

Skript zjistí OS, čip, RAM (na Apple Silicon unified memory, na Linuxu i NVIDIA VRAM)
a spočítá **model budget ≈ 55 % paměťového poolu** — zbytek musí zůstat na KV cache
(roste s kontextovým oknem) a systém.

### Tabulka: paměť → doporučený tier

| Paměťový pool | Budget | Tier | Qwen (review) | Gemma (fast + vision) | Poznámka |
|---|---|---|---|---|---|
| 64 GB+ | ~35 GB+ | XL | `qwen3.6:27b` | `gemma4:26b` | oba drží v paměti naráz |
| 32 GB | ~17 GB | L (referenční) | `qwen3.6:27b` (17 GB) | `gemma4:26b` (17 GB) | modely se STŘÍDAJÍ — po deep běhu čeká další volání ~1–2 min na unload |
| 16 GB | ~8 GB | M | ~8–14B varianta | ~12B varianta | slabší než 27B — udělej si vlastní test (§5) |
| 8 GB | ~4 GB | S | ~4B varianta | ~4B varianta | jen s checklist prompty, čekej chyby |
| < 8 GB | — | žádný | — | — | lokální tier se nevyplatí; citlivé věci zůstávají bez review (NE cloud fallback) |

Konkrétní tagy menších variant se v Ollama registru mění — skript zkouší kandidáty
v pořadí a bere první existující. Když celá řada selže, vyber nejbližší velikost
Qwen/Gemma na ollama.com/library s velikostí souboru ≤ tvůj budget.

## 2. Instalace

```bash
bash scripts/setup-local-llm.sh --install
```

Stáhne doporučené modely a ověří: (a) `OLLAMA_HOST` binding — `0.0.0.0` znamená, že
„lokální" tier je dostupný z LAN → přepni na `127.0.0.1`; (b) vision capability
modelů přes `ollama show` (vision-review.py routuje jen modely, které ji mají).

## 3. Cloud tier — Gemini CLI k lokálnímu LLM

Lokální model je soukromý, ale pomalý a slabší. Gemini dodá rychlý cross-vendor
pohled pro NEcitlivé artefakty (a nejlepší vision oči: 3/3 defektů za 7–13 s).

```bash
npm install -g @google/gemini-cli
# GEMINI_API_KEY do .env v rootu projektu (CLI čte .env z cwd hierarchie!)
echo 'test' | gemini --skip-trust -m gemini-3.5-flash -p "Reply OK if you can read stdin:"
```

Tři zafixované poznatky (nepřeobjevovat):

- headless běh VYŽADUJE `--skip-trust`, jinak CLI odmítne s trusted-directory chybou
- od CLI ~0.49 musí být prompt HODNOTOU `-p` a kontext jde stdinem (stdin se appenduje)
- **free tier Gemini API trénuje na tvých datech** → citlivé artefakty a obrázky NIKDY
  do cloudu; od toho je lokální tier a privacy gate

## 4. Ověření celku (smoke testy)

```bash
# text review lokálně (FIT-FAIL exit 3 = artefakt se nevejde do kontextu — zkrať ho)
printf 'Review this: 2+2=5. Is it correct?' > /tmp/probe.txt
python3 scripts/local-review.py "<tvůj-qwen-tag>" /tmp/probe.txt

# vision lokálně (describe = popis obrázku; qa = PASS/FAIL verdikt, exit 0/2)
python3 scripts/vision-review.py <obrázek.png> --check describe --route local

# privacy gate (exit 2 = SENSITIVE → cloud blokován)
echo 'API_KEY=sk-abcdefghijklmnop' | bash scripts/classify-sensitivity.sh -
```

Pozor u `qwen3.6` třídy: je to thinking model — review trvá 5–8 minut. To je režim
kvality, ne zámrz. Rychlý pass = Gemma (~1 min).

## 5. Vlastní seeded-defect test (10 minut, POVINNÝ krok důvěry)

Benchmarky a názory modelů lžou (ověřeno: predikce se 2× nepotvrdily). Než lokálnímu
modelu svěříš review, změř ho na SVÝCH dokumentech:

1. Vezmi 2–3 své reálné dokumenty (plán, config, návrh).
2. Zasaď do každého 2–4 chyby: špatný součet, protiřečící si sekce, hardcoded
   heslo, vypnutou validaci, špatné datum.
3. Pusť review přes `local-review.py` s checklist promptem (viz níže) a spočítej,
   kolik chyb model našel a co si vymyslel.
4. Recall < ~80 % nebo halucinace → zkus větší model, nebo tier používej jen
   jako „lokální kontrolu omezeného rozsahu", ne jako plnohodnotné review.

**Checklist probes > otevřené „zreviewuj to"** — malým modelům dej konkrétní
ano/ne otázky: sedí všechny součty? odporují si sekce? jsou tu hardcoded secrets?
vypíná něco TLS/validaci? U vision promptů: „projdi všechny 4 okraje obrazu"
(tahle jedna věta zvedla recall z 1/3 na 3/3). Scaffolding je v této velikostní
třídě větší páka než výběr modelu.

## 6. Provozní poznámky

- **Nikdy `ollama run` na dlouhé dokumenty** — tiše ořezává kontext a model
  sebejistě „zreviewuje" text, který nečetl. Vždy `local-review.py` (explicitní
  `num_ctx` + fit-check).
- `num_ctx` default 16384; zvedej jen s ohledem na RAM (KV cache roste s kontextem).
- Výstup lokálního modelu označuj jako „lokální kontrola omezeného rozsahu",
  ne „prošlo review" — kalibruj důvěru čtenáře.
- Citlivé bez dostupného lokálního modelu = review se BLOKUJE. Cloud fallback pro
  citlivá data neexistuje, to je celý smysl privacy gate.
- Vision verdikt je poradní — FAIL vždy potvrď vlastníma očima; obrázek může
  obsahovat adversariální text (prompt injection).

## 7. Troubleshooting

| Symptom | Příčina | Fix |
|---|---|---|
| `local-review.py` exit 3 | artefakt > num_ctx | zkrať/shrň sekce; nikdy neposílej oříznuté |
| review trvá „věčnost" | thinking model | normální (5–8 min); rychlý pass = Gemma |
| `gemini -p` trusted-directory error | chybí `--skip-trust` | přidej flag |
| gemini nevidí API klíč | `.env` mimo cwd | spouštěj z rootu projektu |
| vision-review exit 3 | žádný vision model | `ollama show <tag>` → capability vision; nainstaluj Gemmu |
| druhý lokální běh dlouho startuje | model swap na 32 GB | počkej na unload (~1–2 min), nebo zůstaň u jednoho modelu |
| „local" tier dostupný z LAN | `OLLAMA_HOST=0.0.0.0` | přebinduj na `127.0.0.1` |
