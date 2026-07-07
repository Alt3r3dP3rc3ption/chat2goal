# chat2goal

**chat2goal** is a universal AI skill that transforms messy chat transcripts into rigorous, executable `/goal` loop prompts for agentic models like Anthropic's Fable 5.

Invoke with: `/chat2goal`

## Skills

| Skill | Use when |
|---|---|
| [`chat2goal`](./SKILL.md) | One chat transcript should become a generic executable goal-loop prompt. |
| [`projectChat2goal`](./project-chat2goal/SKILL.md) | Many chats from one ChatGPT/Claude/Codex/Gemini project should become one project-level goal prompt. |
| [`chat2lazyCodex`](./chat2lazycodex/SKILL.md) | One chat transcript should become a LazyCodex/OMO-ready prompt. |
| [`projectChat2lazyCodex`](./project-chat2lazycodex/SKILL.md) | Many project chats should become a LazyCodex/OMO-ready plan or execution prompt. |
| [`skill-universalizer`](./skill-universalizer/SKILL.md) | A finished skill should be packaged into multi-platform release zips. |
| [`plan-council-review`](./plan-council-review/SKILL.md) | A Codex plan should be reviewed by a prompt-only council before it is shown to the user. |

---

## What It Does

Paste any chat transcript and chat2goal will:

1. Extract the primary objective, technical constraints, and desired outputs
2. Restructure everything into a zero-ambiguity initialization prompt using strict headers:
   - `[ROLE]` — defines the agent's identity
   - `[CONTEXT]` — lists all relevant files, schemas, and inputs
   - `[TASK]` — single-sentence goal + constraints + expected outputs
   - `[EXECUTION GATE]` — forces the agent to pause for human review after `/plan`
   - `[DEFINITION OF DONE]` — a specific, testable `/goal` condition

---

## Installation

Download the zip for your platform from [Releases](../../releases/latest):

| Package | Platform |
|---|---|
| `chat2goal-all-platforms.zip` | All platforms (master bundle) |
| `chat2goal-universal.zip` | All platforms in one zip |
| `chat2goal-perplexity.zip` | Perplexity (upload `SKILL.md` directly) |
| `chat2goal-claude.zip` | Claude Web/Desktop Projects + Claude Code CLI |
| `chat2goal-chatgpt.zip` | ChatGPT Custom GPTs |
| `chat2goal-gemini.zip` | Gemini Gems + Gemini CLI + Antigravity CLI (includes `install.bat`) |
| `chat2goal-cursor.zip` | Cursor IDE (`.mdc` rules format) |
| `chat2goal-github-copilot.zip` | GitHub Copilot (VS Code & Visual Studio) |
| `chat2goal-microsoft.zip` | Microsoft Copilot + Copilot Studio |
| `chat2goal-codex.zip` | OpenAI Codex / API |
| `chat2goal-generic.zip` | Generic Python/Node.js orchestrators |

### Quick Install — Gemini CLI & Antigravity (Windows 11)

1. Extract `chat2goal-gemini.zip`
2. Double-click `install.bat`

Copies `system.md` to `%USERPROFILE%\.gemini\` and `AGENTS.md` to `%USERPROFILE%\.config\antigravity\prompts\` automatically.

### Quick Install — Perplexity

1. Extract `chat2goal-perplexity.zip`
2. Go to **Settings → Skills → Upload Skill**
3. Upload `SKILL.md` — frontmatter is read automatically

---

## Building From Source

Requires Python 3.8+. No dependencies.

```bash
python build.py
```

Output zips are written to `chat2goal-dist/`.

Validate skill frontmatter with:

```bash
python scripts/validate_skills.py
```

---

## Roadmap

- `v1.3.0` — **plan council + capability carryover design**: Adds the prompt-only `plan-council-review` skill, documents capability carryover, and parks inactive external-review scripts for future activation.

---

## License

Apache 2.0
