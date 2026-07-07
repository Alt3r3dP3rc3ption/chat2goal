# tool-second-opinion — export pro komunitu (2026-07-06)

Skill pro Claude Code: externí cross-vendor review plánů, kódu, textů a obrázků.
Až 3 revieweři (Claude headless, Gemini CLI, lokální Qwen/Gemma přes Ollama)
+ privacy gate, která citlivá data nikdy nepustí do cloudu.

## Instalace do vlastního projektu

1. Zkopíruj celou složku `tool-second-opinion/` do `.claude/skills/` ve svém projektu.
2. Spusť analýzu svého počítače a instalaci lokálních modelů:
   ```bash
   bash .claude/skills/tool-second-opinion/scripts/setup-local-llm.sh            # doporučení
   bash .claude/skills/tool-second-opinion/scripts/setup-local-llm.sh --install  # stažení
   ```
3. Kompletní návod krok za krokem: `references/runbook-local-llm.md`
   (analýza HW → výběr Qwen+Gemma podle RAM → Gemini CLI cloud tier → smoke testy
   → vlastní seeded-defect test).

## Co je uvnitř

| Soubor | Co dělá |
|---|---|
| `SKILL.md` | workflow skillu (detekce reviewerů, privacy gate, review, syntéza) |
| `references/reviewer-tiers.md` | tabulka tierů, ověřené invokace, měřená čísla z testů |
| `references/runbook-local-llm.md` | instalační runbook podle parametrů TVÉHO počítače |
| `scripts/setup-local-llm.sh` | analýza HW → doporučení/instalace Qwen + Gemma |
| `scripts/classify-sensitivity.sh` | privacy gate (regex scan; exit 2 = jen lokální review) |
| `scripts/local-review.py` | lokální review přes Ollama API (explicitní num_ctx + fit-check) |
| `scripts/vision-review.py` | vision QA obrázků (Gemini / lokální Gemma/Qwen, PASS/FAIL) |
| `docs/*.png` | schémata: jak funguje routing + výsledky srovnávacího testu |

## Než tomu začneš věřit

Čísla v `reviewer-tiers.md` platí pro referenční stroj (Apple Silicon, 32 GB).
Na svém hardwaru si udělej vlastní 10minutový seeded-defect test — postup je
v runbooku §5. Benchmarky a dojmy lžou, měření ne.

## Sanitizace

Export je očištěný od interních identifikátorů autora. Ve
`scripts/classify-sensitivity.sh` doplň vlastní hodnoty na místech
`ADD-YOUR-INTERNAL-HOSTNAME-*` a `ADD-YOUR-INTERNAL-DB-SCHEMA` — gate pak bude
chytat i tvoje interní hostnames a DB schémata.
