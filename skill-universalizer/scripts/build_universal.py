#!/usr/bin/env python3
"""
build_universal.py — skill-universalizer build script

Takes a SKILL.md file and produces platform-specific distribution zips.

Usage:
    python build_universal.py <path/to/SKILL.md> [--output-dir <dir>]

Output:
    <skill-name>-dist/
        <skill-name>-all-platforms.zip   (master bundle)
        <skill-name>-universal.zip
        <skill-name>-perplexity.zip
        <skill-name>-claude.zip
        <skill-name>-chatgpt.zip
        <skill-name>-gemini.zip
        <skill-name>-cursor.zip
        <skill-name>-github-copilot.zip
        <skill-name>-microsoft.zip
        <skill-name>-codex.zip
        <skill-name>-generic.zip
"""

import os
import sys
import re
import zipfile
import shutil
import argparse


# ---------------------------------------------------------------------------
# YAML frontmatter parser (no external deps)
# ---------------------------------------------------------------------------
def parse_frontmatter(text):
    """Extract YAML frontmatter and body from a markdown file."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].strip()
    meta = {}
    current_key = None
    metadata_block = False
    for line in fm_text.splitlines():
        if line.startswith("metadata:"):
            metadata_block = True
            meta["metadata"] = {}
            continue
        if metadata_block:
            m = re.match(r"^\s{2}(\w+):\s*['\"]?(.+?)['\"]?\s*$", line)
            if m:
                meta["metadata"][m.group(1)] = m.group(2)
                continue
            else:
                metadata_block = False
        m = re.match(r"^(\w[\w-]*):\s*['\"]?(.+?)['\"]?\s*$", line)
        if m:
            current_key = m.group(1)
            meta[current_key] = m.group(2)
    return meta, body


# ---------------------------------------------------------------------------
# Install scripts (Gemini/Antigravity Windows 11)
# ---------------------------------------------------------------------------
def make_install_bat(skill_name):
    return f"""@echo off
setlocal

echo.
echo  {skill_name} Installer for Gemini CLI ^& Antigravity CLI
echo  ======================================================
echo.

set "GEMINI_DIR=%USERPROFILE%\\.gemini"
if not exist "%GEMINI_DIR%" mkdir "%GEMINI_DIR%"
copy /Y "gemini_cli\\system.md" "%GEMINI_DIR%\\system.md" >nul
if %errorlevel%==0 (
    echo  [OK] Gemini CLI  ^>  %GEMINI_DIR%\\system.md
) else (
    echo  [FAIL] Could not copy Gemini CLI system.md
)

set "AGY_DIR=%USERPROFILE%\\.config\\antigravity\\prompts"
if not exist "%AGY_DIR%" mkdir "%AGY_DIR%"
copy /Y "antigravity_cli\\AGENTS.md" "%AGY_DIR%\\AGENTS.md" >nul
if %errorlevel%==0 (
    echo  [OK] Antigravity  ^>  %AGY_DIR%\\AGENTS.md
) else (
    echo  [FAIL] Could not copy Antigravity AGENTS.md
)

echo.
echo  Gemini CLI: set GEMINI_SYSTEM_MD=1 then run: gemini
echo  Antigravity: AGENTS.md auto-loads from project root.
echo.
pause
endlocal
"""


def make_install_ps1(skill_name):
    return f"""# {skill_name} Installer for Gemini CLI & Antigravity CLI
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host ""
Write-Host " {skill_name} Installer for Gemini CLI & Antigravity CLI"
Write-Host " ======================================================"
Write-Host ""

$geminiDir = "$env:USERPROFILE\\.gemini"
if (-not (Test-Path $geminiDir)) {{ New-Item -ItemType Directory -Path $geminiDir | Out-Null }}
Copy-Item -Force "gemini_cli\\system.md" "$geminiDir\\system.md"
Write-Host " [OK] Gemini CLI  >  $geminiDir\\system.md"

$agyDir = "$env:USERPROFILE\\.config\\antigravity\\prompts"
if (-not (Test-Path $agyDir)) {{ New-Item -ItemType Directory -Path $agyDir -Force | Out-Null }}
Copy-Item -Force "antigravity_cli\\AGENTS.md" "$agyDir\\AGENTS.md"
Write-Host " [OK] Antigravity  >  $agyDir\\AGENTS.md"

Write-Host ""
Write-Host " Gemini CLI: `$env:GEMINI_SYSTEM_MD = '1'; gemini"
Write-Host " Antigravity: copy AGENTS.md to your project root."
Write-Host ""
Read-Host "Press Enter to exit"
"""


# ---------------------------------------------------------------------------
# README templates
# ---------------------------------------------------------------------------
def make_readme(skill_name, version, platform_label, install_steps):
    return f"""# {skill_name} v{version} — {platform_label} Installation

Invoke with: `/{skill_name}`

## Installation

{install_steps}
"""


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------
def build(skill_md_path, output_dir=None):
    with open(skill_md_path, "r", encoding="utf-8") as f:
        raw = f.read()

    meta, body = parse_frontmatter(raw)

    name = meta.get("name", os.path.splitext(os.path.basename(skill_md_path))[0])
    description = meta.get("description", f"A skill named {name}.")
    license_id = meta.get("license", "Apache-2.0")
    version = meta.get("metadata", {}).get("version", "1.0.0") if isinstance(meta.get("metadata"), dict) else "1.0.0"

    print(f"Building universal packages for: {name} v{version}")

    # Clean description (strip surrounding quotes if present)
    description = description.strip('"\'')

    # Platform content variants
    standard = body

    perplexity_content = f"""---
name: {name}
description: "{description}"
license: {license_id}
metadata:
  version: '{version}'
  author: {name}
---
{body}"""

    copilot_content = f"""---
description: "{description} v{version}"
---
{body}"""

    cursor_content = f"""---
description: "{description} Invoke with /{name}. v{version}"
alwaysApply: false
---
{body}"""

    # Output directory
    dist_dir = output_dir or f"{name}-dist"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    packages = {
        f"{name}-universal": {
            "files": {
                "perplexity/SKILL.md": perplexity_content,
                "gemini/gem_instructions.txt": standard,
                "gemini_cli/system.md": standard,
                "antigravity_cli/AGENTS.md": standard,
                "chatgpt/custom_gpt_instructions.txt": standard,
                "claude_web_and_desktop/project_instructions.txt": standard,
                "claude_code_cli/CLAUDE.md": standard,
                f"cursor_ide/{name}.mdc": cursor_content,
                "openai_codex/system_message.txt": standard,
                f"github_copilot/{name}.prompt.md": copilot_content,
                "microsoft_copilot/prompt_gallery.txt": standard,
                "generic_orchestrator/{}_system_prompt.md".format(name): standard,
            },
            "readme": make_readme(name, version, "Universal",
                "This package contains files for all supported platforms.\n"
                "See the platform-specific zips for focused install instructions."),
            "scripts": None,
        },
        f"{name}-perplexity": {
            "files": {"SKILL.md": perplexity_content},
            "readme": make_readme(name, version, "Perplexity",
                "1. Go to **Settings → Skills → Upload Skill**.\n"
                "2. Upload `SKILL.md` from this folder. Perplexity reads the YAML frontmatter automatically."),
            "scripts": None,
        },
        f"{name}-claude": {
            "files": {
                "claude_web_and_desktop/project_instructions.txt": standard,
                "claude_code_cli/CLAUDE.md": standard,
            },
            "readme": make_readme(name, version, "Claude",
                "**Web & Desktop Projects:** New Project → Add Custom Instructions → paste `project_instructions.txt`.\n\n"
                "**Claude Code CLI:** Copy `CLAUDE.md` to your project root. Auto-loaded at session start."),
            "scripts": None,
        },
        f"{name}-chatgpt": {
            "files": {"custom_gpt_instructions.txt": standard},
            "readme": make_readme(name, version, "ChatGPT",
                "1. ChatGPT → Explore → Create a GPT → Configure.\n"
                "2. Paste `custom_gpt_instructions.txt` into the Instructions box."),
            "scripts": None,
        },
        f"{name}-gemini": {
            "files": {
                "gemini/gem_instructions.txt": standard,
                "gemini_cli/system.md": standard,
                "antigravity_cli/AGENTS.md": standard,
            },
            "readme": make_readme(name, version, "Gemini & Antigravity CLI",
                "**Windows 11 Quick Install:** Double-click `install.bat`.\n\n"
                "**Gemini Web:** Gems → New Gem → paste `gemini/gem_instructions.txt`.\n\n"
                "**Gemini CLI:** Copy `gemini_cli/system.md` to `.gemini/system.md` in your project, "
                "then `set GEMINI_SYSTEM_MD=1` before running `gemini`.\n\n"
                "**Antigravity CLI:** Copy `antigravity_cli/AGENTS.md` to your project root. Auto-loaded at session start."),
            "scripts": {
                "install.bat": make_install_bat(name),
                "install.ps1": make_install_ps1(name),
            },
        },
        f"{name}-cursor": {
            "files": {f"{name}.mdc": cursor_content},
            "readme": make_readme(name, version, "Cursor IDE",
                f"1. Copy `{name}.mdc` into your project's `.cursor/rules/` folder.\n"
                f"2. In Cursor chat, type `/{name}` to invoke."),
            "scripts": None,
        },
        f"{name}-github-copilot": {
            "files": {f"{name}.prompt.md": copilot_content},
            "readme": make_readme(name, version, "GitHub Copilot",
                f"1. Copy `{name}.prompt.md` into `.github/prompts/`.\n"
                f"2. In Copilot Chat, type `/{name}`."),
            "scripts": None,
        },
        f"{name}-microsoft": {
            "files": {"prompt_gallery.txt": standard},
            "readme": make_readme(name, version, "Microsoft Copilot",
                "**Prompt Gallery:** Paste `prompt_gallery.txt`, run once, bookmark it.\n\n"
                "**Copilot Studio:** Agents → Tools → Add new Prompt → paste `prompt_gallery.txt`."),
            "scripts": None,
        },
        f"{name}-codex": {
            "files": {"system_message.txt": standard},
            "readme": make_readme(name, version, "OpenAI Codex / API",
                "Inject `system_message.txt` into the `role: \"system\"` payload of your API request."),
            "scripts": None,
        },
        f"{name}-generic": {
            "files": {f"{name}_system_prompt.md": standard},
            "readme": make_readme(name, version, "Generic Orchestrator",
                f"Load `{name}_system_prompt.md` as the system prompt in your Python or Node.js agent."),
            "scripts": None,
        },
    }

    zip_paths = []

    for pkg_name, config in packages.items():
        base_dir = os.path.join(dist_dir, pkg_name)
        os.makedirs(base_dir)

        # README
        with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(config["readme"])

        # Files
        for rel_path, content in config["files"].items():
            full_path = os.path.join(base_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Scripts
        if config.get("scripts"):
            for script_name, script_content in config["scripts"].items():
                with open(os.path.join(base_dir, script_name), "w", encoding="utf-8", newline="\r\n") as f:
                    f.write(script_content)

        # Zip
        zip_path = os.path.join(dist_dir, f"{pkg_name}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    fp = os.path.join(root, file)
                    arcname = os.path.relpath(fp, os.path.dirname(base_dir))
                    zipf.write(fp, arcname)
        zip_paths.append(zip_path)
        print(f"  Built: {pkg_name}.zip")

    # Master bundle
    master = os.path.join(dist_dir, f"{name}-all-platforms.zip")
    with zipfile.ZipFile(master, "w", zipfile.ZIP_DEFLATED) as zipf:
        for zp in zip_paths:
            zipf.write(zp, os.path.basename(zp))
    print(f"  Built: {name}-all-platforms.zip (master bundle)")
    print(f"\nDone. Output: {dist_dir}/")
    return dist_dir


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build universal platform zips from a SKILL.md")
    parser.add_argument("skill_md", help="Path to the input SKILL.md file")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: <skill-name>-dist)")
    args = parser.parse_args()

    if not os.path.exists(args.skill_md):
        print(f"Error: file not found: {args.skill_md}")
        sys.exit(1)

    build(args.skill_md, args.output_dir)
