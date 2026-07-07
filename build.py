import os
import zipfile
import shutil

VERSION = "1.3.0"

# ---------------------------------------------------------------------------
# PROMPT BODY
# ---------------------------------------------------------------------------
PROMPT_BODY = """[SYSTEM ROLE]
You are `chat2goal`, an expert Multi-Agent Orchestrator and Prompt Engineer. Your objective is to analyze the provided chat transcript, distill the core project requirements, and generate a single, highly structured prompt for Anthropic's Fable 5.

[INPUT]
{{chat_transcript}}

[PROCESSING RULES]
1. Context Extraction: Identify the primary objective, all technical constraints, reference materials, and desired file outputs discussed in the transcript.
2. Structure: Build a self-contained initialization prompt using strict headers ([ROLE], [CONTEXT], [TASK], [EXECUTION GATE], [DEFINITION OF DONE]) so the new Fable 5 session has zero ambiguity.
3. Gate Enforcement: Ensure the instructions explicitly state that the model must stop after presenting the plan and await human validation.

[OUTPUT FORMAT]
You must output ONLY a single markdown code block containing the complete, ready-to-paste text. Do not include any introductory or concluding conversational filler.

Format the output exactly like this:

```text
[ROLE]
You are an autonomous expert software engineer and systems architect.

[CONTEXT]
The following inputs, files, and schemas are relevant to this task:
- [List of files, schemas, or data structures]

[TASK]
I need you to complete the following objective: [Clear, single-sentence goal].

Please review the specifications below and execute `/plan` to map out your implementation strategy.
- [Constraint 1]
- [Constraint 2]
- Expected Output: [Exact file names and formats to be generated]

[EXECUTION GATE]
CRITICAL: After generating your plan via `/plan`, you must immediately pause and await human review. Do NOT initiate the `/goal` loop or write any implementation files until the user explicitly responds with "Approved" or provides feedback on your strategy.

[DEFINITION OF DONE]
When the user gives the approval to proceed, the autonomous loop will be managed under the following criteria:
/goal [Insert highly specific, testable condition. e.g., "script builds without errors, exits with code 0, and output.json perfectly matches the schema requirements."]
```
"""

ROOT_SKILL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SKILL.md")
with open(ROOT_SKILL_PATH, "r", encoding="utf-8") as f:
    ROOT_SKILL_CONTENT = f.read()

parts = ROOT_SKILL_CONTENT.split("---", 2)
STANDARD_CONTENT = parts[2].lstrip() if len(parts) == 3 else ROOT_SKILL_CONTENT

# Perplexity: SKILL.md with versioned frontmatter
PERPLEXITY_SKILL_CONTENT = ROOT_SKILL_CONTENT

# GitHub Copilot
GITHUB_COPILOT_CONTENT = f"""---
description: "Compiles messy chat transcripts into rigorous, executable goal-loop prompts for agentic coding models. v{VERSION}"
---
""" + STANDARD_CONTENT

# Cursor
CURSOR_CONTENT = f"""---
description: "Compiles messy chat transcripts into rigorous, executable goal-loop prompts for agentic coding models. Invoke with /chat2goal. v{VERSION}"
alwaysApply: false
---
""" + STANDARD_CONTENT

# ---------------------------------------------------------------------------
# INSTALL SCRIPTS
# ---------------------------------------------------------------------------

GEMINI_INSTALL_BAT = r"""@echo off
setlocal

echo.
echo  chat2goal Installer for Gemini CLI ^& Antigravity CLI
echo  ======================================================
echo.

:: ---------- Gemini CLI ----------
set "GEMINI_DIR=%USERPROFILE%\.gemini"
if not exist "%GEMINI_DIR%" mkdir "%GEMINI_DIR%"

copy /Y "gemini_cli\system.md" "%GEMINI_DIR%\system.md" >nul
if %errorlevel%==0 (
    echo  [OK] Gemini CLI  ^>  %GEMINI_DIR%\system.md
) else (
    echo  [FAIL] Could not copy Gemini CLI system.md
)

:: ---------- Antigravity CLI ----------
set "AGY_DIR=%USERPROFILE%\.config\antigravity\prompts"
if not exist "%AGY_DIR%" mkdir "%AGY_DIR%"

copy /Y "antigravity_cli\AGENTS.md" "%AGY_DIR%\AGENTS.md" >nul
if %errorlevel%==0 (
    echo  [OK] Antigravity  ^>  %AGY_DIR%\AGENTS.md
) else (
    echo  [FAIL] Could not copy Antigravity AGENTS.md
)

echo.
echo  Gemini CLI: run these commands before starting a session:
echo    set GEMINI_SYSTEM_MD=1
echo    gemini
echo.
echo  Antigravity: copy AGENTS.md to any project root for auto-loading,
echo  or reference it via your CLI pipeline config.
echo.
pause
endlocal
"""

GEMINI_INSTALL_PS1 = r"""# chat2goal Installer for Gemini CLI & Antigravity CLI
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host ""
Write-Host " chat2goal Installer for Gemini CLI & Antigravity CLI"
Write-Host " ======================================================"
Write-Host ""

# Gemini CLI
$geminiDir = "$env:USERPROFILE\.gemini"
if (-not (Test-Path $geminiDir)) { New-Item -ItemType Directory -Path $geminiDir | Out-Null }
Copy-Item -Force "gemini_cli\system.md" "$geminiDir\system.md"
Write-Host " [OK] Gemini CLI  >  $geminiDir\system.md"

# Antigravity CLI
$agyDir = "$env:USERPROFILE\.config\antigravity\prompts"
if (-not (Test-Path $agyDir)) { New-Item -ItemType Directory -Path $agyDir -Force | Out-Null }
Copy-Item -Force "antigravity_cli\AGENTS.md" "$agyDir\AGENTS.md"
Write-Host " [OK] Antigravity  >  $agyDir\AGENTS.md"

Write-Host ""
Write-Host " Gemini CLI: run these commands before starting a session:"
Write-Host "   `$env:GEMINI_SYSTEM_MD = '1'"
Write-Host "   gemini"
Write-Host ""
Write-Host " Antigravity: copy AGENTS.md to any project root for auto-loading."
Write-Host ""
Read-Host "Press Enter to exit"
"""

# ---------------------------------------------------------------------------
# README TEMPLATES
# ---------------------------------------------------------------------------

README_UNIVERSAL = f"""# chat2goal v{VERSION} — Universal Installation Package

chat2goal is a system skill that takes messy chat transcripts and compiles them into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Platform-Specific Packages

| Package | Platforms |
|---|---|
| chat2goal-perplexity.zip | Perplexity |
| chat2goal-claude.zip | Claude Web, Claude Desktop, Claude Code CLI |
| chat2goal-chatgpt.zip | ChatGPT Custom GPTs |
| chat2goal-gemini.zip | Gemini Custom Gems, Gemini CLI, Antigravity CLI |
| chat2goal-cursor.zip | Cursor IDE |
| chat2goal-github-copilot.zip | GitHub Copilot (VS Code & Visual Studio) |
| chat2goal-microsoft.zip | Microsoft Copilot, Copilot Studio |
| chat2goal-codex.zip | OpenAI Codex / API |
| chat2goal-generic.zip | Generic Python/Node.js Orchestrators |

## Installation by Platform

**Perplexity**
1. In Perplexity, go to Settings -> Skills -> Upload Skill.
2. Upload `perplexity/SKILL.md` directly. Perplexity reads the YAML frontmatter automatically.

**Gemini CLI & Antigravity CLI (Windows 11)**
1. Extract the zip, open `gemini_cli+antigravity/`, and double-click `install.bat`.
   - Installs `system.md` to `%USERPROFILE%\\.gemini\\`
   - Installs `AGENTS.md` to `%USERPROFILE%\\.config\\antigravity\\prompts\\`
2. For Gemini CLI, set `GEMINI_SYSTEM_MD=1` before starting a session.

**Gemini (Web / Custom Gems)**
1. Open Gemini -> "Gems" -> "New Gem". Name it `chat2goal`.
2. Paste the contents of `gemini/gem_instructions.txt`.

**ChatGPT (Custom GPTs)**
1. ChatGPT -> Explore -> Create a GPT -> Configure.
2. Paste `chatgpt/custom_gpt_instructions.txt` into the Instructions box.

**Claude (Web & Desktop Projects)**
1. New Project -> Add Custom Instructions.
2. Paste `claude_web_and_desktop/project_instructions.txt`.

**Claude Code (CLI)**
1. Copy `claude_code_cli/CLAUDE.md` into your project root.

**Cursor IDE**
1. Copy `cursor_ide/chat2goal.mdc` into `.cursor/rules/` in your project root.
2. Invoke with `/chat2goal` in Cursor chat.

**GitHub Copilot**
1. Copy `github_copilot/chat2goal.prompt.md` into `.github/prompts/`.
2. Invoke with `/chat2goal` in Copilot Chat.

**Microsoft Copilot**
1. Prompt Gallery: Paste `microsoft_copilot/prompt_gallery.txt`, run once, bookmark it.
2. Copilot Studio: Agents -> Tools -> Add new Prompt.

**OpenAI Codex**
1. Inject `openai_codex/system_message.txt` into the `role: "system"` payload.

**Generic Orchestrators**
1. Use `generic_orchestrator/chat2goal_system_prompt.md` in your agent definitions.
"""

README_GEMINI = f"""# chat2goal v{VERSION} — Gemini & Antigravity CLI Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Quick Install (Windows 11)

Double-click **`install.bat`** to automatically copy files to the correct locations:
- Gemini CLI: `%USERPROFILE%\\.gemini\\system.md`
- Antigravity CLI: `%USERPROFILE%\\.config\\antigravity\\prompts\\AGENTS.md`

Or run the PowerShell version:
```
powershell -ExecutionPolicy Bypass -File install.ps1
```

## Manual Installation

### Gemini Web (Custom Gems)
1. Open Gemini -> **"Gems" -> "New Gem"**. Name it `chat2goal`.
2. Paste the contents of `gemini/gem_instructions.txt`.

### Gemini CLI (project-level)
1. Copy `gemini_cli/system.md` to your project's `.gemini/` folder:
   ```
   your-project/.gemini/system.md
   ```
2. Start a session with:
   ```
   set GEMINI_SYSTEM_MD=1
   gemini
   ```

### Antigravity CLI
1. Copy `antigravity_cli/AGENTS.md` to your project root.  
   Antigravity auto-loads it at session start.
2. Config lives at: `%USERPROFILE%\\.gemini\\antigravity-cli\\settings.json`
"""

README_PERPLEXITY = f"""# chat2goal v{VERSION} — Perplexity Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Installation

1. In Perplexity, go to **Settings -> Skills -> Upload Skill**.
2. Upload `SKILL.md` from this folder directly.  
   Perplexity reads the YAML frontmatter automatically — no copy/paste needed.

Once uploaded, type `/chat2goal` followed by your chat transcript.
"""

README_CLAUDE = f"""# chat2goal v{VERSION} — Claude Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Claude Web & Desktop (Projects)
1. New Project -> **"Add Custom Instructions"**.
2. Paste `claude_web_and_desktop/project_instructions.txt`.

## Claude Code (CLI)
1. Copy `claude_code_cli/CLAUDE.md` into your **project root**.  
   Claude Code auto-loads it at session start:
   ```
   your-project/
   └── CLAUDE.md
   ```
"""

README_CHATGPT = f"""# chat2goal v{VERSION} — ChatGPT Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Custom GPT
1. ChatGPT -> **"Explore" -> "Create a GPT" -> "Configure"**.
2. Paste `custom_gpt_instructions.txt` into the **"Instructions"** box and save.
"""

README_CURSOR = f"""# chat2goal v{VERSION} — Cursor IDE Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Installation
1. Copy `chat2goal.mdc` into your project's `.cursor/rules/` folder:
   ```
   your-project/
   └── .cursor/
       └── rules/
           └── chat2goal.mdc
   ```
2. In Cursor chat, type `/chat2goal` to invoke it.

> Note: The modern Cursor format uses `.mdc` files in `.cursor/rules/`. The legacy `.cursorrules` root file is deprecated.
"""

README_GITHUB_COPILOT = f"""# chat2goal v{VERSION} — GitHub Copilot Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Installation (VS Code & Visual Studio)
1. Copy `chat2goal.prompt.md` into `.github/prompts/`:
   ```
   your-project/
   └── .github/
       └── prompts/
           └── chat2goal.prompt.md
   ```
2. In Copilot Chat, type `/chat2goal`.
"""

README_MICROSOFT = f"""# chat2goal v{VERSION} — Microsoft Copilot Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Prompt Gallery
1. Paste `prompt_gallery.txt`, run once, click the **bookmark icon** to save.

## Copilot Studio
1. Agents -> Tools -> Add a tool -> **Add new Prompt**.
2. Paste `prompt_gallery.txt` and save.
"""

README_CODEX = f"""# chat2goal v{VERSION} — OpenAI Codex / API Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Installation
Inject `system_message.txt` into the `role: "system"` payload:

```python
import openai

with open("system_message.txt", "r") as f:
    system_prompt = f.read()

response = openai.chat.completions.create(
    model="codex-mini-latest",
    messages=[
        {{"role": "system", "content": system_prompt}},
        {{"role": "user", "content": "{{chat_transcript}}"}}
    ]
)
```
"""

README_GENERIC = f"""# chat2goal v{VERSION} — Generic Orchestrator Installation

chat2goal compiles messy chat transcripts into rigorous, executable /goal prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Installation
Load `chat2goal_system_prompt.md` as the system prompt in your agent:

```python
with open("chat2goal_system_prompt.md", "r") as f:
    system_prompt = f.read()
# Pass system_prompt to your agent/LLM initialization
```
"""

# ---------------------------------------------------------------------------
# PACKAGE DEFINITIONS
# ---------------------------------------------------------------------------
PACKAGES = {
    "chat2goal-universal": {
        "readme": README_UNIVERSAL,
        "files": {
            "perplexity/SKILL.md": PERPLEXITY_SKILL_CONTENT,
            "gemini/gem_instructions.txt": STANDARD_CONTENT,
            "gemini_cli/system.md": STANDARD_CONTENT,
            "antigravity_cli/AGENTS.md": STANDARD_CONTENT,
            "chatgpt/custom_gpt_instructions.txt": STANDARD_CONTENT,
            "claude_web_and_desktop/project_instructions.txt": STANDARD_CONTENT,
            "claude_code_cli/CLAUDE.md": STANDARD_CONTENT,
            "cursor_ide/chat2goal.mdc": CURSOR_CONTENT,
            "openai_codex/system_message.txt": STANDARD_CONTENT,
            "github_copilot/chat2goal.prompt.md": GITHUB_COPILOT_CONTENT,
            "microsoft_copilot/prompt_gallery.txt": STANDARD_CONTENT,
            "generic_orchestrator/chat2goal_system_prompt.md": STANDARD_CONTENT,
        },
        "scripts": None,  # no install scripts in universal (platform-specific zips handle it)
    },
    "chat2goal-perplexity": {
        "readme": README_PERPLEXITY,
        "files": {
            "SKILL.md": PERPLEXITY_SKILL_CONTENT,
        },
        "scripts": None,
    },
    "chat2goal-claude": {
        "readme": README_CLAUDE,
        "files": {
            "claude_web_and_desktop/project_instructions.txt": STANDARD_CONTENT,
            "claude_code_cli/CLAUDE.md": STANDARD_CONTENT,
        },
        "scripts": None,
    },
    "chat2goal-chatgpt": {
        "readme": README_CHATGPT,
        "files": {
            "custom_gpt_instructions.txt": STANDARD_CONTENT,
        },
        "scripts": None,
    },
    "chat2goal-gemini": {
        "readme": README_GEMINI,
        "files": {
            "gemini/gem_instructions.txt": STANDARD_CONTENT,
            "gemini_cli/system.md": STANDARD_CONTENT,
            "antigravity_cli/AGENTS.md": STANDARD_CONTENT,
        },
        "scripts": {
            "install.bat": GEMINI_INSTALL_BAT,
            "install.ps1": GEMINI_INSTALL_PS1,
        },
    },
    "chat2goal-cursor": {
        "readme": README_CURSOR,
        "files": {
            "chat2goal.mdc": CURSOR_CONTENT,
        },
        "scripts": None,
    },
    "chat2goal-github-copilot": {
        "readme": README_GITHUB_COPILOT,
        "files": {
            "chat2goal.prompt.md": GITHUB_COPILOT_CONTENT,
        },
        "scripts": None,
    },
    "chat2goal-microsoft": {
        "readme": README_MICROSOFT,
        "files": {
            "prompt_gallery.txt": STANDARD_CONTENT,
        },
        "scripts": None,
    },
    "chat2goal-codex": {
        "readme": README_CODEX,
        "files": {
            "system_message.txt": STANDARD_CONTENT,
        },
        "scripts": None,
    },
    "chat2goal-generic": {
        "readme": README_GENERIC,
        "files": {
            "chat2goal_system_prompt.md": STANDARD_CONTENT,
        },
        "scripts": None,
    },
}

# ---------------------------------------------------------------------------
# BUILD
# ---------------------------------------------------------------------------
def create_packages():
    # Use a path relative to this script so it works on any machine/CI runner
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat2goal-dist")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    for package_name, config in PACKAGES.items():
        base_dir = os.path.join(output_dir, package_name)
        os.makedirs(base_dir)

        # Write README
        with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(config["readme"])

        # Write content files
        for rel_path, content in config["files"].items():
            full_path = os.path.join(base_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Write install scripts at zip root (if any)
        if config.get("scripts"):
            for script_name, script_content in config["scripts"].items():
                script_path = os.path.join(base_dir, script_name)
                with open(script_path, "w", encoding="utf-8", newline="\r\n") as f:
                    f.write(script_content)

        # Zip
        zip_path = os.path.join(output_dir, f"{package_name}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(base_dir))
                    zipf.write(file_path, arcname)

        print(f"  Built: {package_name}.zip")

    # Master bundle
    master_zip = os.path.join(output_dir, "chat2goal-all-platforms.zip")
    with zipfile.ZipFile(master_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for fname in sorted(os.listdir(output_dir)):
            if fname.endswith(".zip") and fname != "chat2goal-all-platforms.zip":
                zipf.write(os.path.join(output_dir, fname), fname)

    print(f"  Built: chat2goal-all-platforms.zip (master bundle)")
    print(f"\nAll packages written to {output_dir}/")
    return output_dir

if __name__ == "__main__":
    create_packages()
