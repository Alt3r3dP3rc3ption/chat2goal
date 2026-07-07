#!/usr/bin/env python3
"""Vision QA review — cloud (Gemini) / local (Ollama) routing with privacy gate.

Vzniklo 2026-07-05 z měřeného srovnání (4 úlohy, ground truth ze zdrojáků):
Gemini 3.5 Flash našel 3/3 zanesených defektů za 7-13 s; gemma4:26b 2/3 za ~25 s;
qwen3.6:27b 2/3 za ~3 min (thinking). Nikdo nevyrobil false positive. Klíčem ke
3/3 byl edge-checklist v promptu (projdi všechny 4 okraje) — proto je zabudovaný.

Routing:
  --route auto   (default) NON-sensitive: Gemini → fallback gemma4 lokálně
  --route cloud  jen Gemini (gemini-3.5-flash přes CLI, vyžaduje --skip-trust)
  --route local  jen lokální rychlý model (gemma4*)
  --route deep   jen lokální thinking model (qwen3.6*) — pomalejší, na citlivé + důkladné
  --sensitive    HARD gate: nikdy cloud (ani ve fallbacku). Kombinace s --route cloud = chyba.

Obrázky nejde regex-skenovat jako text (classify-sensitivity.sh) — sensitivitu
určuje VOLAJÍCÍ podle Step 1.5 SKILL.md (klientská data, produkce, PII => --sensitive).
POZOR free tier Gemini API trénuje na datech — citlivé vizuály VŽDY --sensitive.

Usage: vision-review.py <image> [--check qa|fit|describe] [--route auto|cloud|local|deep]
                        [--sensitive] [--context "co je to za asset"] [--lang cz|en]
Exit:  0 PASS (nebo describe hotovo) · 2 FAIL (defekt nalezen — validní nález, ne chyba)
       1 usage / gate violation · 3 žádný dostupný backend · 4 verdikt neparsovatelný
"""
import argparse, base64, json, os, pathlib, re, subprocess, sys, time, urllib.request, uuid

OLLAMA = "http://127.0.0.1:11434"
GEMINI_MODEL = "gemini-3.5-flash"
# vision-capable kandidáti, rychlé první; skutečná dostupnost se ověřuje přes /api/show
LOCAL_FAST_PREFIXES = ("gemma4", "qwen3-vl", "llava", "minicpm")
LOCAL_DEEP_PREFIXES = ("qwen3.6", "qwen3-vl")
CLI_NOISE = ("Warning:", "Ripgrep is not available", "[STARTUP]", "Loaded cached credentials",
             "(node:", "(Use `node")

PROMPTS = {
    ("qa", "cz"): (
        "Jsi QA kontrolor grafiky před publikací. Zkontroluj přiložený obrázek na vizuální defekty. "
        "Postupuj systematicky:\n"
        "1) Projdi VŠECHNY ČTYŘI OKRAJE obrazu — je někde text nebo grafický prvek uříznutý hranou?\n"
        "2) Přetéká někde text mimo svůj rámeček nebo vyhrazenou plochu?\n"
        "3) Nechybí očekávané části layoutu (patička, logo, stránkování, CTA)?\n"
        "4) Nepřekrývají se prvky tak, že jsou nečitelné?\n"
        "První řádek odpovědi: PASS (bez defektu) nebo FAIL (defekt nalezen). "
        "Pak stručně česky: co přesně je špatně a kde."
    ),
    ("qa", "en"): (
        "You are a pre-publish graphics QA reviewer. Check the attached image for visual defects. "
        "Work systematically:\n"
        "1) Scan ALL FOUR EDGES — is any text or element clipped by the image border?\n"
        "2) Does any text overflow its box or allotted area?\n"
        "3) Are expected layout parts missing (footer, logo, pagination, CTA)?\n"
        "4) Do elements overlap illegibly?\n"
        "First line of your answer: PASS (no defect) or FAIL (defect found). "
        "Then briefly: what exactly is wrong and where."
    ),
    ("fit", "cz"): (
        "Jsi QA kontrolor. Tento vizuál vznikl PŘEKLADEM z jiného jazyka — přeložený text bývá delší "
        "a přetéká. Zkontroluj systematicky:\n"
        "1) Přetéká nebo je uříznutý některý textový blok (projdi všechny čtyři okraje i rámečky)?\n"
        "2) Je někde text zalomený uprostřed slova nebo nakrčený menším písmem, než má okolí?\n"
        "3) Zůstal někde nepřeložený text původního jazyka?\n"
        "První řádek odpovědi: PASS nebo FAIL. Pak stručně: co a kde."
    ),
    ("fit", "en"): (
        "You are a QA reviewer. This visual was TRANSLATED from another language — translated text is "
        "often longer and overflows. Check systematically:\n"
        "1) Does any text block overflow or get clipped (scan all four edges and boxes)?\n"
        "2) Is text broken mid-word anywhere, or squeezed into a smaller font than its surroundings?\n"
        "3) Any leftover untranslated source-language text?\n"
        "First line: PASS or FAIL. Then briefly: what and where."
    ),
    ("describe", "cz"): "Popiš přiložený obrázek: layout, veškeré texty (přesně, se zachovanou diakritikou), barvy, grafické prvky.",
    ("describe", "en"): "Describe the attached image: layout, all text (exactly as written), colors, graphic elements.",
}


def die(msg, code):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def ollama_vision_models():
    """Vrať instalované tagy s vision capability (ověřeno přes /api/show, ne hádáno)."""
    try:
        tags = json.loads(urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read())
    except Exception:
        return []
    out = []
    for m in tags.get("models", []):
        name = m.get("name", "")
        base = name.split("/")[-1]  # tagy mohou mít registry prefix (library/gemma4:latest)
        if not base.lower().startswith(tuple(LOCAL_FAST_PREFIXES + LOCAL_DEEP_PREFIXES)):
            continue
        try:
            body = json.dumps({"model": name}).encode()
            req = urllib.request.Request(f"{OLLAMA}/api/show", data=body,
                                         headers={"Content-Type": "application/json"})
            info = json.loads(urllib.request.urlopen(req, timeout=5).read())
            if "vision" in info.get("capabilities", []):
                out.append(name)
        except Exception:
            continue
    return out


def pick_local(models, prefixes):
    for p in prefixes:
        for m in models:
            if m.split("/")[-1].lower().startswith(p):
                return m
    return None


def run_ollama(model, image_path, prompt, num_ctx):
    img_b64 = base64.b64encode(pathlib.Path(image_path).read_bytes()).decode()
    body = json.dumps({
        "model": model, "prompt": prompt, "images": [img_b64], "stream": False,
        "keep_alive": "3m", "options": {"num_ctx": num_ctx, "temperature": 0.2},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    data = json.loads(urllib.request.urlopen(req, timeout=900).read())
    sys.stderr.write(f"[local | {model} | {time.time()-t0:.0f}s]\n")
    return data.get("response", "").strip()


def run_gemini(image_path, prompt):
    # DVĚ pasti @-příloh v gemini CLI (obě ověřeny 2026-07-05):
    # 1) @cesta mimo cwd CLI tiše nahradí JINÝM souborem z disku a model sebejistě popíše
    #    cizí obrázek — @-parser bere jen relativní cesty uvnitř workspace.
    # 2) cwd měnit nelze: CLI čte GEMINI_API_KEY z .env v cwd hierarchii (spouštěj z rootu
    #    agentic-os). Řešení: cwd nechat, obrázek mimo cwd dočasně zkopírovat dovnitř.
    #    Mezery v názvu rozbíjejí @-parser → řeší stejná dočasná kopie.
    img = pathlib.Path(image_path).resolve()
    cwd = pathlib.Path.cwd()
    tmp, name = None, None
    try:
        name = str(img.relative_to(cwd))
    except ValueError:
        pass
    if name is None or " " in name:
        # pid+uuid: paralelní běhy ve stejné vteřině nesmí sdílet temp soubor (TOCTOU)
        tmp = cwd / f".vr-tmp-{os.getpid()}-{uuid.uuid4().hex[:8]}{img.suffix}"
        tmp.write_bytes(img.read_bytes())
        name = tmp.name
    cmd = ["gemini", "--skip-trust", "-m", GEMINI_MODEL, "-p", f"@{name} {prompt}"]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gemini CLI exit {proc.returncode}: {proc.stderr.strip()[:300]}")
    lines = [l for l in proc.stdout.splitlines()
             if l.strip() and not any(l.strip().startswith(n) for n in CLI_NOISE)]
    sys.stderr.write(f"[cloud | {GEMINI_MODEL} | {time.time()-t0:.0f}s]\n")
    return "\n".join(lines).strip()


def parse_verdict(text):
    """PASS/FAIL z prvních řádků odpovědi (modely občas předřadí prázdný řádek/nadpis).

    Celá slova s hranicemi — "PASSING" nematchne, "FAIL (defekt)" ano. Řádek obsahující
    OBĚ slova ("PASS/FAIL: FAIL" hlavička) je ambivalentní → přeskočit, rozhodne další řádek.
    """
    for line in text.splitlines()[:3]:
        words = set(re.findall(r"\b(PASS|FAIL)\b", line.upper()))
        if words == {"PASS"}:
            return "PASS"
        if words == {"FAIL"}:
            return "FAIL"
    return None


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("image")
    ap.add_argument("--check", choices=["qa", "fit", "describe"], default="qa")
    ap.add_argument("--route", choices=["auto", "cloud", "local", "deep"], default="auto")
    ap.add_argument("--sensitive", action="store_true")
    ap.add_argument("--context", default="")
    ap.add_argument("--lang", choices=["cz", "en"], default="cz")
    ap.add_argument("--num-ctx", type=int, default=16384)
    a = ap.parse_args()

    img = pathlib.Path(a.image)
    if not img.is_file():
        die(f"error: obrázek nenalezen: {img}", 1)
    if a.sensitive and a.route == "cloud":
        die("GATE: --sensitive + --route cloud je porušení privacy gate. Citlivé vizuály "
            "jdou POUZE lokálně (--route local|deep|auto).", 1)

    prompt = PROMPTS[(a.check, a.lang)]
    if a.context:
        prompt += f"\n\nKontext k assetu: {a.context}" if a.lang == "cz" else f"\n\nAsset context: {a.context}"

    # pořadí backendů podle routy + privacy
    attempts = []  # (kind, model)
    locals_avail = ollama_vision_models()
    fast = pick_local(locals_avail, LOCAL_FAST_PREFIXES)
    deep = pick_local(locals_avail, LOCAL_DEEP_PREFIXES)
    if a.route in ("cloud", "auto") and not a.sensitive:
        attempts.append(("cloud", GEMINI_MODEL))
    if a.route in ("local", "auto"):
        local_model = fast or deep  # fast preferovaný; deep-only instalace nesmí skončit exit 3
        if local_model:
            attempts.append(("local", local_model))
    if a.route == "deep" and deep:
        attempts.append(("local", deep))

    if not attempts:
        die("error: žádný dostupný backend pro zvolenou routu (gemini CLI / vision model v Ollama). "
            f"Lokální vision modely nalezeny: {locals_avail or 'žádné'}", 3)

    answer, errors = None, []
    for kind, model in attempts:
        try:
            answer = run_gemini(img, prompt) if kind == "cloud" else run_ollama(model, img, prompt, a.num_ctx)
            if answer:
                break
            errors.append(f"{kind}/{model}: prázdná odpověď")
        except Exception as e:
            errors.append(f"{kind}/{model}: {e}")
            sys.stderr.write(f"[fallback] {kind}/{model} selhal: {e}\n")

    if not answer:
        die("error: všechny backendy selhaly:\n  " + "\n  ".join(errors), 3)

    print(answer)
    if a.check == "describe":
        return
    verdict = parse_verdict(answer)
    if verdict == "PASS":
        sys.exit(0)
    if verdict == "FAIL":
        sys.exit(2)
    sys.stderr.write("warn: verdikt PASS/FAIL nenalezen na prvních řádcích odpovědi\n")
    sys.exit(4)


if __name__ == "__main__":
    main()
