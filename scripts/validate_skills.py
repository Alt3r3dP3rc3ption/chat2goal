#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "SKILL.md": "chat2goal",
    "project-chat2goal/SKILL.md": "project-chat2goal",
    "chat2lazycodex/SKILL.md": "chat2lazycodex",
    "project-chat2lazycodex/SKILL.md": "project-chat2lazycodex",
    "skill-universalizer/SKILL.md": "skill-universalizer",
}

for rel, expected_name in REQUIRED.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, re.MULTILINE)
    assert match, f"{rel}: missing lowercase name frontmatter"
    assert match.group(1) == expected_name, f"{rel}: expected {expected_name}, got {match.group(1)}"
    assert "description:" in text, f"{rel}: missing description"
    assert "metadata:" in text, f"{rel}: missing metadata"

print(f"validated {len(REQUIRED)} skills")
