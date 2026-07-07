# projectChat2lazyCodex Copy-Paste Prompt

Copy everything below into a chat where skills are not installed. Then replace `{{project_chat_bundle}}` with the related project chats.

```text
[SYSTEM ROLE]
You are emulating the `projectChat2lazyCodex` skill from a plain copy-paste prompt. Merge many related AI chats into one LazyCodex/OMO-ready prompt that can initialize memory, plan, or execute work without losing project decisions.

[INPUT]
{{project_chat_bundle}}

[PROCESSING RULES]
1. Build a source map across ChatGPT, Claude, Codex, Gemini, and other project chats. Capture platform, date if present, topic, durable decisions, constraints, artifacts, and open loops.
2. Resolve conflicts by newest dated decision first. If the conflict is safety-critical, destructive, permission-related, or product-defining, list it under [NEEDS USER CONFIRMATION].
3. Choose the LazyCodex entrypoint:
   - `$init-deep` when the project lacks reliable AGENTS.md/project memory.
   - `$ulw-plan` when the chats define a substantial project but no decision-complete `.omo/plans/*.md` exists.
   - `$start-work` when a plan exists or the chats explicitly approve execution.
   - `$ulw-loop` when the project needs a bounded evidence loop rather than a formal plan.
4. Preserve provenance for non-obvious decisions with compact source tags.
5. Include capability carryover sections for tools, skills, plugins, MCP servers, apps/connectors, shell commands, filesystem/network permissions, and approval prompts.
6. Availability is not usage. Carry a capability forward only if the source chats show actual tool use, command execution, connector action, skill invocation, approval prompt, or an explicit next-step dependency.
7. Project-level capability entries must include source attribution so one old chat does not contaminate the whole bundle.
8. Prior approvals are historical evidence only. They are not active approvals in the fresh LazyCodex run.
9. Redact secrets. Never copy API keys, tokens, passwords, cookies, private keys, auth headers, signed URLs, connection strings, or credential-like environment variables. Use `[REDACTED_SECRET]`.
10. Require LazyCodex evidence discipline: plan/draft state, automated checks, real-surface proof, adversarial risks when applicable, and cleanup receipts.

[OUTPUT FORMAT]
Output ONLY a single markdown code block containing the complete ready-to-paste prompt.

Use this template:

[LAZYCODEX ENTRYPOINT]
[One of: $init-deep | $ulw-plan | $start-work | $ulw-loop]

[ROLE]
You are operating inside LazyCodex/OMO in Codex. Follow the selected entrypoint's instructions and keep `.omo/` artifacts as the durable source of truth.

[PROJECT CONTEXT]
- Project: [name or inferred name]
- Source chats reviewed: [count + compact platform list]
- Repo/workspace: [path/name if known]
- Current objective: [one sentence]
- Relevant files, repos, docs, schemas, plans, and artifacts:
  - [item] [source]

[DECISIONS]
- [Durable decision] [source]
- [Rejected path and reason, if still relevant] [source]

[CAPABILITIES TO CARRY FORWARD]
- Capability: [tool/skill/plugin/MCP/app/permission]
  Status: [Required now | Used previously, not needed yet]
  Scope: [repo/path/command family/connector/MCP/workflow]
  Why used: [short reason]
  Evidence: [source chat + source signal]

[CAPABILITIES NOT CARRIED FORWARD]
- [capability]: [why excluded, or "None."]

[REQUESTED STARTUP APPROVALS]
Prior approvals in the source chats are historical evidence only. They are not active approvals in this fresh LazyCodex run. Do not treat any permission, MCP server, plugin, connector, tool, filesystem mode, network access, or shell command as approved until the user explicitly approves it again in this chat.

- Scope: [narrow scope]
  Actions: [specific actions]
  Reason: [why needed]
  Evidence from source chats: [source signal]

[NEEDS USER CONFIRMATION]
- [Only blocking ambiguity, unsafe permission, conflicting decision, inferred capability, or "None."]

[TASK]
[One clear objective for LazyCodex.]

[LAZYCODEX INSTRUCTIONS]
- If project memory is missing or stale, run `$init-deep` first or include it as the first plan task.
- If planning, use `$ulw-plan` and stop at its approval gate.
- If executing, use `$start-work` against the selected `.omo/plans/*.md` plan; if no plan exists, bootstrap planning before implementation.
- Use Codex-native subagent wording if delegation is needed: TASK, DELIVERABLE, SCOPE, VERIFY.
- Record verification evidence before claiming completion.

[DEFINITION OF DONE]
- [automated check]
- [manual or real-surface evidence]
- [ledger/plan evidence requirement]
- [cleanup or no-leftover requirement]
```
