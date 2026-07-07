# inactive/tool-second-opinion

This folder is a parked copy of `2026-07-06_tool-second-opinion-export.zip` for future external-review activation work.

It is inactive:
- Do not package it in release zips.
- Do not call these scripts from `plan-council-review`.
- Do not install dependencies for it as part of normal chat2goal builds.
- Keep the original skill text as `SKILL.inactive.md`, not `SKILL.md`, so recursive skill installers do not publish it accidentally.

Current `build.py` uses explicit package file lists, so this folder is not included in generated release zips.
