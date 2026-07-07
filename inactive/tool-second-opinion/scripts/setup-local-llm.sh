#!/usr/bin/env bash
# setup-local-llm.sh — analyze THIS machine and recommend (or install) the right
# local LLM pair for tool-second-opinion: a Qwen (quality/thinking review tier)
# and a Gemma (fast review + local vision tier).
#
# Every machine is different — the author's reference setup (32 GB Apple Silicon)
# runs qwen3.6:27b + gemma4:26b, but a 16 GB or 8 GB machine needs smaller
# variants. This script measures RAM/GPU and picks the largest tier that fits.
#
# Usage:
#   setup-local-llm.sh              # analyze + recommend only (no downloads)
#   setup-local-llm.sh --install    # analyze, recommend, and pull the models
#
# Sizing rule of thumb (why the thresholds below):
#   - Ollama needs the model file in RAM/VRAM + KV cache + OS headroom.
#   - Budget ≈ 55 % of unified RAM (Apple Silicon) or GPU VRAM (NVIDIA).
#   - A ~27B dense model ≈ 17 GB file → needs a 32 GB machine.
#   - Two 17 GB models do NOT fit a 32 GB machine at once — they swap in turns
#     (works fine, costs ~1-2 min unload wait between tiers).
#
# Model candidates are tried IN ORDER and the first tag that exists in the
# Ollama registry wins — tags change over time, so edit the lists below if
# everything in a tier 404s (check https://ollama.com/library for current tags).

set -uo pipefail

MODE="recommend"
[ "${1:-}" = "--install" ] && MODE="install"

# ── 1. Detect hardware ─────────────────────────────────────────────────────────
OS="$(uname -s)"
RAM_GB=0
CHIP="unknown"
VRAM_GB=0

if [ "$OS" = "Darwin" ]; then
  RAM_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
  CHIP="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)"
  case "$CHIP" in *Apple*) UNIFIED=1 ;; *) UNIFIED=0 ;; esac
elif [ "$OS" = "Linux" ]; then
  RAM_GB=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
  CHIP="$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo | sed 's/^ //')"
  UNIFIED=0
  if command -v nvidia-smi >/dev/null 2>&1; then
    VRAM_GB=$(( $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1) / 1024 ))
  fi
else
  echo "Unsupported OS: $OS (macOS + Linux only)" >&2; exit 1
fi

# Effective budget: unified memory (Apple) or VRAM (NVIDIA) or plain RAM (CPU-only)
if [ "${UNIFIED:-0}" = "1" ]; then
  POOL=$RAM_GB; POOL_KIND="unified RAM (Apple Silicon)"
elif [ "$VRAM_GB" -gt 0 ]; then
  POOL=$VRAM_GB; POOL_KIND="GPU VRAM (NVIDIA)"
else
  POOL=$RAM_GB; POOL_KIND="system RAM (CPU-only — expect SLOW inference)"
fi
BUDGET_GB=$(( POOL * 55 / 100 ))

echo "── Machine analysis ──────────────────────────────────────────"
echo "OS:            $OS"
echo "Chip:          $CHIP"
echo "RAM:           ${RAM_GB} GB"
[ "$VRAM_GB" -gt 0 ] && echo "GPU VRAM:      ${VRAM_GB} GB"
echo "Memory pool:   ${POOL} GB ($POOL_KIND)"
echo "Model budget:  ~${BUDGET_GB} GB (55 % of pool; rest = KV cache + OS)"
echo ""

# ── 2. Pick the tier ───────────────────────────────────────────────────────────
# Each tier: QWEN candidates (quality review, thinking) + GEMMA candidates
# (fast review + vision). First tag that pulls successfully wins.
if [ "$BUDGET_GB" -ge 34 ]; then
  TIER="XL (both models can stay loaded together)"
  QWEN_CANDIDATES=("qwen3.6:27b")
  GEMMA_CANDIDATES=("gemma4:26b")
elif [ "$BUDGET_GB" -ge 16 ]; then
  TIER="L — the verified reference setup (~27B class, models swap in turns)"
  QWEN_CANDIDATES=("qwen3.6:27b")
  GEMMA_CANDIDATES=("gemma4:26b")
elif [ "$BUDGET_GB" -ge 8 ]; then
  TIER="M (~8-14B class) — good reviews, weaker than 27B; run your own seeded-defect test"
  QWEN_CANDIDATES=("qwen3.6:14b" "qwen3.6:8b" "qwen3:14b" "qwen3:8b")
  GEMMA_CANDIDATES=("gemma4:12b" "gemma3:12b" "gemma3n:e4b")
elif [ "$BUDGET_GB" -ge 3 ]; then
  TIER="S (~4B class) — usable ONLY with checklist-style prompts; expect misses"
  QWEN_CANDIDATES=("qwen3.6:4b" "qwen3:4b")
  GEMMA_CANDIDATES=("gemma3:4b" "gemma3n:e2b")
else
  echo "VERDICT: <8 GB usable memory — a local review tier is not worth it here."
  echo "Use the cloud tiers only (Claude baseline + Gemini) and treat sensitive"
  echo "artefacts as UNREVIEWABLE on this machine (do not fall back to cloud)."
  exit 0
fi

echo "── Recommendation ────────────────────────────────────────────"
echo "Tier:   $TIER"
echo "Qwen  (quality/thinking review): ${QWEN_CANDIDATES[*]}  <- first available wins"
echo "Gemma (fast review + vision):    ${GEMMA_CANDIDATES[*]}  <- first available wins"
echo ""
echo "Note: tags are candidates, not gospel — Ollama tags change. If a whole"
echo "tier fails to pull, pick the closest Qwen/Gemma size at ollama.com/library"
echo "that is <= ${BUDGET_GB} GB file size, then re-run your own seeded-defect test."
echo ""

if [ "$MODE" = "recommend" ]; then
  echo "Dry run done. Re-run with --install to download."
  exit 0
fi

# ── 3. Install ─────────────────────────────────────────────────────────────────
if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: ollama not installed. Get it at https://ollama.com/download, then re-run." >&2
  exit 1
fi

pull_first() { # pull_first <label> <candidates...>  — prints the winning tag on stdout
  local label="$1"; shift
  for tag in "$@"; do
    echo ">> trying $label candidate: $tag" >&2
    if ollama pull "$tag" >&2; then echo "OK: $tag installed" >&2; echo "$tag"; return 0; fi
  done
  echo "WARN: no $label candidate could be pulled — pick one manually at ollama.com/library" >&2
  return 1
}

QWEN_TAG="$(pull_first "Qwen" "${QWEN_CANDIDATES[@]}")" || QWEN_TAG=""
GEMMA_TAG="$(pull_first "Gemma" "${GEMMA_CANDIDATES[@]}")" || GEMMA_TAG=""

# ── 4. Verify ──────────────────────────────────────────────────────────────────
echo ""
echo "── Verification ──────────────────────────────────────────────"
BIND="${OLLAMA_HOST:-127.0.0.1:11434}"
case "$BIND" in
  0.0.0.0*) echo "WARN: OLLAMA_HOST=$BIND — reachable from your LAN. Rebind to 127.0.0.1 before trusting the 'local/private' tier." ;;
  *)        echo "OK: Ollama bound to $BIND (localhost = private)" ;;
esac

for tag in "$QWEN_TAG" "$GEMMA_TAG"; do
  [ -n "$tag" ] || continue
  CAPS="$(ollama show "$tag" 2>/dev/null | grep -A5 -i capabilities || true)"
  if echo "$CAPS" | grep -qi vision; then
    echo "OK: $tag has VISION capability (usable by vision-review.py)"
  else
    echo "note: $tag has no vision capability (text review only)"
  fi
done

echo ""
echo "Done. Next steps (see references/runbook-local-llm.md):"
echo "  1) optional cloud tier: npm install -g @google/gemini-cli  + GEMINI_API_KEY in .env"
echo "  2) smoke test:  python3 scripts/local-review.py <tag> <promptfile>"
echo "  3) vision test: python3 scripts/vision-review.py <image> --check describe --route local"
echo "  4) run YOUR OWN seeded-defect test before trusting any local model (runbook §5)"
