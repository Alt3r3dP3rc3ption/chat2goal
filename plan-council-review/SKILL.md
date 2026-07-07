---
name: plan-council-review
description: "Runs a prompt-only Codex plan review council before presenting a plan for user review. Use when an agent has drafted a plan and wants at least five independent reviewers, optional large-plan teams, and a privacy-gated route for outside council support."
license: Apache-2.0
metadata:
  version: '1.0.0'
  author: chat2goal
---

# plan-council-review

## Use When

Use this skill before showing a plan to the user when:
- A plan has meaningful risk, ambiguity, architecture impact, security/privacy concerns, cost impact, or multi-step execution.
- The user asks for a plan review, council, second opinion, outside review, red-team review, or reviewers.
- The plan is large enough that one reviewer pass is likely to miss issues.

Do not use it for trivial one-line edits, pure formatting, or questions where no plan will be presented.

## Guardrails

- Prompt-only: do not install hooks, call external tools, or modify files as part of this skill.
- Recursion guard: never ask a council to review the council process, this skill text, or another council's prompt. If a reviewer asks for another council, summarize the gap yourself instead.
- Minimum council: use at least five direct reviewers for normal plans.
- Large-plan team mode: for broad plans, use teams of six: one lead plus five reviewer members per team. The main agent sends only the scope, a task summary of 200 words or fewer, and the plan to each lead. Leads brief their own members.
- Privacy gate: classify the review material before sharing. Sensitive material includes secrets, credentials, personal data, private business data, proprietary code, unreleased strategy, regulated data, or customer data.
- External/cloud council is opt-in or high-stakes only. Sensitive material routes local-only. If sensitive material requires outside review and no local backend exists, block and ask the user for a sanitized summary, local backend, or explicit scope change.

## Council Flow

1. Build a council packet:
   - Scope: files, modules, systems, or decisions under review.
   - Task summary: 200 words or fewer.
   - Plan: the exact plan being reviewed.
   - Review bar: correctness, missing risks, smaller alternatives, tests, rollout, and user-facing clarity.
2. Privacy gate the packet:
   - If sensitive: local-only review, no external/cloud route.
   - If not sensitive and the user asked for outside support, offer the outside council route.
   - If high-stakes and not sensitive, the main agent may suggest outside support but must not send anything externally without opt-in.
3. Select review shape:
   - Normal: five direct reviewers.
   - Large: one or more teams of six, each with one lead and five members.
4. Collect critiques, deduplicate, and return only actionable changes.
5. Update the plan before presenting it to the user, or state why a critique was rejected.

## Direct Reviewer Prompt

```text
You are reviewer {number} in a five-person plan council.

Scope:
{scope}

Task summary (<=200 words):
{task_summary}

Plan:
{plan}

Review for: incorrect assumptions, missing steps, security/privacy risk, test gaps, simpler alternatives, and rollout hazards.

Return:
- Top issues, ordered by severity
- One smaller alternative if it exists
- Tests or checks that would catch failure
- Verdict: accept, accept with changes, or reject
```

## Large-Plan Lead Prompt

```text
You are the lead for a six-person plan review team: you plus five reviewers.

Scope:
{scope}

Task summary (<=200 words):
{task_summary}

Plan:
{plan}

Brief five reviewers yourself. Assign each a different focus: correctness, architecture, security/privacy, testing/operations, and simplicity/YAGNI.

Return one consolidated review:
- Critical blockers
- Important improvements
- What to delete or simplify
- Verification gaps
- Team verdict: accept, accept with changes, or reject
```

## Outside Council Route

Use only when the user asks for external/outside review or when the work is high-stakes and the user opts in.

```text
Outside council request:
- Backend: local-only, external/cloud, or user-selected
- Sensitivity: non-sensitive only for external/cloud
- Scope: {scope}
- Task summary (<=200 words): {task_summary}
- Plan: {plan}

If sensitivity is unclear, stop and ask for classification before sending.
If sensitive and no local backend exists, block instead of sending externally.
```

## Final Review Summary

```text
Council result:
- Verdict: {verdict}
- Plan changes made:
  - {change}
- Rejected critiques:
  - {critique} -> {reason}
- Remaining risks:
  - {risk}
- Checks to run:
  - {check}
```
