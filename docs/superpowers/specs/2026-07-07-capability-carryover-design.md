# Capability Carryover Design

## Purpose

`chat2goal`, `projectChat2goal`, `chat2lazyCodex`, and `projectChat2lazyCodex` should preserve the capabilities that mattered in the source chat or project bundle when they generate a prompt for a fresh chat. The fresh chat needs enough startup context to continue the workflow, but it must not inherit stale tools, ambient environment noise, secrets, or old approval state.

## Scope

This change is prompt-only. No transcript parser, manifest schema, or extraction script is required for this version.

The four chat2goal-family skills will add processing rules and output sections for:

- capabilities to carry forward
- capabilities not carried forward
- requested startup approvals
- permission carryover limits
- secret safety
- needs-user-confirmation items

The LazyCodex variants will frame these sections as startup context for a new LazyCodex/OMO run, not as inherited permissions.

## Active Capability Rule

Availability is not usage. A capability listed in system context, installed-tool lists, environment dumps, plugin metadata, stale config, or model boilerplate must be excluded unless the source transcript shows actual use or an explicit next-step dependency.

A capability may be carried forward only when the source shows at least one of:

- a tool call, command execution, MCP interaction, connector action, or skill invocation
- a concrete workflow step that directly depended on the capability
- an explicit user instruction that the fresh chat must use that capability next

Each carried capability must include:

- `Capability`: tool, MCP server, plugin, skill, app/connector, permission, shell access, filesystem mode, network access, or repo/workspace assumption
- `Status`: `Required now` or `Used previously, not needed yet`
- `Scope`: narrow repo, path, command family, connector, MCP server, account, or workflow boundary
- `Why used`: short reason
- `Evidence`: source chat name/date when available plus the observed tool call, command, approval prompt, or workflow dependency

Project-level variants must include source attribution for each capability so one old chat cannot contaminate the whole bundle.

## Capabilities Not Carried Forward

Generated prompts must include a section for capabilities that are deliberately excluded. This section should contain stale, failed, broken, ambient, mentioned-only, irrelevant, or environment-noise capabilities when they appear in the source material.

Examples:

- an MCP server listed in startup context but never used
- a plugin mentioned in instructions but not invoked
- a command suggested but never run
- a connector that failed auth and was not needed later
- a broad filesystem/network mode shown in metadata without workflow evidence

## Permission Carryover Limits

Prior approvals in the source transcript are historical evidence only. They are not active approvals in the fresh chat. The generated prompt must not treat any permission, MCP server, plugin, connector, tool, filesystem mode, network access, or shell command as approved until the user explicitly approves it again in the fresh chat.

Do not call the section `approved permissions`. Use `REQUESTED STARTUP APPROVALS`.

## Requested Startup Approvals

The generated prompt should ask the user to approve or narrow a scoped bundle before work begins. Approval requests must be supported by source-transcript evidence and must be least-privilege.

Each requested approval must include:

- `Scope`
- `Actions`
- `Reason`
- `Evidence from source chat`

Approval requests must not ask for broader permissions than the transcript proves were needed. Prefer scoped nouns such as a specific repo, path, command family, connector, workflow, or MCP server. Avoid generic language like "approve all tools" or "grant full filesystem/network access."

Destructive, credential-bearing, account-wide, organization-wide, billing, deployment, permission-changing, or repo-mutating approvals require fresh explicit confirmation and belong under `NEEDS USER CONFIRMATION` unless the user clearly asks to approve them in the fresh chat.

## Needs User Confirmation

This section is mandatory. Use it for anything inferred from prose, ambiguous, destructive, credential-bearing, account-wide, organization-wide, stale, failed, or broader than the evidence proves.

Destructive actions include delete, overwrite, reset, force-push, production deploy, billing changes, permission changes, credential rotation, and equivalent irreversible or high-impact operations.

## Secret Safety

Generated prompts must never copy secrets from source transcripts. Redact API keys, tokens, passwords, cookies, session IDs, private keys, auth headers, signed URLs, connection strings, and credential-like environment variables.

Use `[REDACTED_SECRET]` and describe only the type of secret needed. Do not include token lengths, prefixes, suffixes, or enough surrounding data to reconstruct the secret.

## Output Section Template

Generic variants should add these sections to the generated prompt:

```text
[CAPABILITIES TO CARRY FORWARD]
- Capability: [name/type]
  Status: [Required now | Used previously, not needed yet]
  Scope: [repo/path/command family/connector/MCP/workflow]
  Why used: [short reason]
  Evidence: [source signal]

[CAPABILITIES NOT CARRIED FORWARD]
- [capability]: [why excluded]

[REQUESTED STARTUP APPROVALS]
Prior approvals in the source transcript are historical evidence only. They are not active approvals in this fresh chat. Do not treat any permission, MCP server, plugin, connector, tool, filesystem mode, network access, or shell command as approved until the user explicitly approves it again in this chat.

- Scope: [narrow scope]
  Actions: [specific actions]
  Reason: [why needed]
  Evidence from source chat: [source signal]

[NEEDS USER CONFIRMATION]
- [item, or "None."]

[SECRET SAFETY]
Secrets from the source transcript were redacted. Required secret types, if any:
- [secret type or "None."]
```

LazyCodex variants should include the same sections after `[PROJECT CONTEXT]` or `[CONTEXT]`, and before `[LAZYCODEX INSTRUCTIONS]`. The wording must say these are startup requests for the new LazyCodex run, not inherited permissions.

## Rejected Alternatives

Helper script extractor: rejected for now because transcript formats vary across ChatGPT, Claude, Codex, Gemini, and exported project bundles. A script would add brittle parsing before there is evidence manual extraction fails repeatedly.

Full manifest schema: rejected for now because these skills are designed for messy pasted chats. Requiring a structured manifest would make the common case harder.

## Verification

Implementation should be verified with:

- `python scripts/validate_skills.py`
- `python build.py`
- a small generated-output smoke check showing the new sections appear in built Codex, Cursor, GitHub Copilot, and Perplexity package outputs

No new runtime dependency is needed.
