#!/usr/bin/env bash
# classify-sensitivity.sh — HARD privacy gate for tool-second-opinion.
#
# Scans an artefact / assembled-context file for sensitivity markers. If any
# HIGH-confidence marker matches, cloud reviewers (Gemini + Claude baseline) MUST
# be skipped and the review routed to the LOCAL Qwen tier only.
#
# This is the technical enforcement behind Step 1.5's privacy gate. It is
# deliberately tuned to FAIL TOWARD LOCAL: a false positive only forces an
# unnecessary local review (safe, just slower); a false negative would leak data
# to a cloud vendor (unacceptable). When in doubt, it flags.
#
# Usage:
#   classify-sensitivity.sh <file>          # scan a file
#   cat context.md | classify-sensitivity.sh -   # scan stdin
#
# Exit codes (consumed by the skill):
#   0  CLEAR      — no HIGH-confidence markers; cloud reviewers allowed
#   2  SENSITIVE  — HIGH-confidence marker(s) found; LOCAL Qwen only
#   1  usage / read error
#
# Output (stdout), machine + human readable:
#   VERDICT: SENSITIVE|CLEAR
#   matched: <comma-separated HIGH categories>      (only if any)
#   warn:    <comma-separated SOFT categories+counts> (only if any)
#
# NOTE: regex-based, not semantic. It catches shapes (key=, sk-…, 10.x, /clients/,
# conn strings, "confidential"), not meaning. The human still classifies in
# Step 1.5 — this script can only make the decision STRICTER, never looser.

set -uo pipefail

src="${1:-}"
if [ -z "$src" ]; then
  echo "usage: classify-sensitivity.sh <file|->" >&2
  exit 1
fi
if [ "$src" = "-" ]; then
  content="$(cat)"
elif [ -f "$src" ]; then
  content="$(cat "$src")"
else
  echo "error: no such file: $src" >&2
  exit 1
fi

high=()   # HIGH-confidence → hard block
soft=()   # SOFT → reported, contributes only in volume

# match <label> <ERE>  → adds to high[] if found
match() {
  if printf '%s' "$content" | LC_ALL=C grep -qEi "$2" 2>/dev/null; then
    high+=("$1")
  fi
}

# count <label> <ERE> <threshold> → soft note always; promotes to high[] if count >= threshold
count() {
  local n
  n="$(printf '%s' "$content" | LC_ALL=C grep -oEi "$2" 2>/dev/null | wc -l | tr -d ' ')"
  if [ "${n:-0}" -ge "$3" ]; then
    high+=("$1(${n})")
  elif [ "${n:-0}" -gt 0 ]; then
    soft+=("$1(${n})")
  fi
}

# ── HIGH-confidence markers (any one → SENSITIVE) ──────────────────────────────
match "secret-keyvar" '([A-Z0-9_]*(API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|PRIVATE[_-]?KEY)[A-Z0-9_]*)[[:space:]]*[=:]'
match "secret-prefix" '(sk-[A-Za-z0-9]{12,}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16})'
match "private-key"   'BEGIN[[:space:][:punct:]]*(RSA|EC|OPENSSH|PGP|DSA)?[[:space:][:punct:]]*PRIVATE[[:space:]]+KEY'
match "bearer"        '(authorization:[[:space:]]*bearer[[:space:]]|bearer[[:space:]]+[A-Za-z0-9._-]{20,})'
match "conn-string"   '(postgres(ql)?|mysql|mongodb(\+srv)?|redis|amqp)://[^[:space:]]+'
match "internal-ip"   '(\b10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b|\b192\.168\.[0-9]{1,3}\.[0-9]{1,3}\b|\b172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}\b)'
match "internal-host" '(ADD-YOUR-INTERNAL-HOSTNAME-1|ADD-YOUR-INTERNAL-HOSTNAME-2|_smb\._tcp|[A-Za-z0-9_-]+\._smb\._tcp\.local)'
match "client-path"   '((^|[^A-Za-z])clients/|brand_context/|ADD-YOUR-INTERNAL-DB-SCHEMA\.[a-z_]+)'
match "explicit-mark" '(SENSITIVE|CONFIDENTIAL|INTERNAL[ _-]ONLY|DO[ _-]NOT[ _-]SHARE|NEPOS[IÍ]LAT|D[UŮ]V[EĚ]RN|INTERN[IÍ])'
# CZ PII/finanční identifikátory (přidáno 2026-07-05 po cross-vendor review — Gemini Flash
# našel díru: české citlivé tvary chyběly úplně). RČ: YYMMDD/XXXX, měsíc 01-12 nebo 51-62
# (ženy +50); lomítko volitelné — 9-10místné číslo validního tvaru je RČ-shaped i bez něj.
match "cz-rodne-cislo" '[0-9]{2}(0[1-9]|1[0-2]|5[1-9]|6[0-2])(0[1-9]|[12][0-9]|3[01])/?[0-9]{3,4}([^0-9]|$)'
match "cz-ico-dic"    '(IČO|IČ|ICO|DIČ|DIC)[[:space:].:]*(CZ)?[0-9]{8}([^0-9]|$)'
match "cz-bank-ucet"  '(CZ[0-9]{2}[0-9 ]{20,26}|[0-9]{1,6}-[0-9]{2,10}/[0-9]{4}([^0-9]|$)|[0-9]{6,10}/(0100|0300|0600|0710|0800|2010|2700|3030|5500|6210)([^0-9]|$))'

# ── SOFT markers (incidental alone; a LIST of them → SENSITIVE) ────────────────
# A single email/phone is likely incidental (a trailer, an example). Three or more
# looks like a contact / lead dump → promote to SENSITIVE.
count "email" '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' 3
count "phone" '(\+420[[:space:]]?)?[0-9]{3}[[:space:]]?[0-9]{3}[[:space:]]?[0-9]{3}' 3
# CZ smluvně/finanční kontext: jedna zmínka je běžná (marketingový text o teambuildingu),
# opakovaný výskyt = dokument O konkrétní smlouvě/faktuře/mzdě → lokálně.
count "cz-business-doc" '(smlouv|faktur[ay]|objednávk|cenov[áa][[:space:]]+nabídk|mzd[ayě]|rodn[ée][[:space:]]+číslo|výplat)' 3

if [ "${#high[@]}" -gt 0 ]; then
  echo "VERDICT: SENSITIVE"
  echo "matched: $(IFS=', '; echo "${high[*]}")"
  [ "${#soft[@]}" -gt 0 ] && echo "warn: $(IFS=', '; echo "${soft[*]}")"
  exit 2
else
  echo "VERDICT: CLEAR"
  [ "${#soft[@]}" -gt 0 ] && echo "warn: $(IFS=', '; echo "${soft[*]}")"
  exit 0
fi
