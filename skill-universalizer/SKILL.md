---
name: skill-universalizer
description: "Takes any SKILL.md file or .skill.zip and packages it into a multi-platform distribution with platform-specific zips for Perplexity, Claude, ChatGPT, Gemini CLI, Antigravity CLI, Cursor, GitHub Copilot, Microsoft Copilot, OpenAI Codex, and generic orchestrators. Use when the user has a finished skill and wants to distribute it across all major AI platforms. Triggers on phrases like 'package my skill', 'make it universal', 'distribute this skill', 'create platform zips', or when a SKILL.md or .skill.zip is provided."
license: Apache-2.0
metadata:
  version: '1.1.0'
  author: chat2goal
---

# skill-universalizer

## When to Use This Skill

Load this skill when the user:
- Provides a `SKILL.md` file or `.skill.zip` and wants it packaged for multiple AI platforms
- Says "make my skill universal", "package this for all platforms", "distribute my skill"
- Wants to create platform-specific install zips from a single skill definition

## What It Does

Takes a single `SKILL.md` (or extracts one from a `.skill.zip`) and produces:
- One zip per major platform with the correctly named file and any required frontmatter
- A master bundle zip containing all platform zips
- Platform-specific READMEs with focused install instructions

## Instructions

### Step 1 — Locate the Input

Check for input in this order:
1. A file attachment in the conversation (`.skill.zip` or `SKILL.md`)
2. A file path the user provided
3. Ask the user to provide the `SKILL.md` or `.skill.zip`

If a `.skill.zip` is provided, extract it and locate the `SKILL.md` inside.

### Step 2 — Parse the Skill

Read the `SKILL.md` and extract:
- `name` from YAML frontmatter — used for file naming and zip names
- `description` from YAML frontmatter — carried into platform-specific frontmatter
- `license` from YAML frontmatter (default to `Apache-2.0` if absent)
- `metadata.version` from YAML frontmatter (default to `1.0.0` if absent)
- The full markdown body (everything after the closing `---`)

### Step 3 — Run the Build Script

Execute `build_universal.py` (included in this skill's `scripts/` folder) by:
1. Saving the extracted `SKILL.md` to the workspace as `input_skill.md`
2. Running: `python scripts/build_universal.py input_skill.md`
3. The script outputs zips to `{skill-name}-dist/`

### Step 4 — Validate the Perplexity Package

Run agentskills validation on the output:
```bash
# Copy SKILL.md into a correctly named directory for validation
mkdir -p /tmp/{skill-name}
cp {skill-name}-dist/{skill-name}-perplexity/SKILL.md /tmp/{skill-name}/SKILL.md
agentskills validate /tmp/{skill-name}/
```

Fix any validation errors before proceeding.

### Step 5 — Share the Output

1. Share `{skill-name}-all-platforms.zip` as the primary download
2. List all generated platform zips so the user knows what was created
3. Offer to push to a GitHub repo if the user has one

## Platform File Naming Reference

| Platform | Correct Filename | Location in zip |
|---|---|---|
| Perplexity | `SKILL.md` | zip root |
| Claude Code CLI | `CLAUDE.md` | `claude_code_cli/` |
| Claude Web/Desktop | `project_instructions.txt` | `claude_web_and_desktop/` |
| Gemini CLI | `system.md` | `gemini_cli/` |
| Antigravity CLI | `AGENTS.md` | `antigravity_cli/` |
| Gemini Web | `gem_instructions.txt` | `gemini/` |
| Cursor IDE | `{name}.mdc` | `cursor_ide/` |
| GitHub Copilot | `{name}.prompt.md` | `github_copilot/` |
| Microsoft Copilot | `prompt_gallery.txt` | `microsoft_copilot/` |
| OpenAI Codex | `system_message.txt` | `openai_codex/` |
| Generic | `{name}_system_prompt.md` | `generic_orchestrator/` |

## Notes

- Gemini zip always includes `install.bat` and `install.ps1` for Windows 11 auto-install
- GitHub Copilot and Cursor files require YAML frontmatter with at minimum a `description` field
- Perplexity `SKILL.md` must pass `agentskills validate` before being included
- The `name` field in frontmatter must be lowercase alphanumeric with hyphens only (validated by agentskills)
