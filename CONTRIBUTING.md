# Contributing to chat2goal

Thanks for your interest in contributing. This project is intentionally simple — a single skill prompt packaged for every major AI platform.

## Ways to Contribute

- **Bug reports** — If a platform package installs incorrectly or a file is named wrong, open an issue with the platform name and what you expected vs. what happened.
- **New platform support** — If a platform isn't covered yet, open an issue or PR with the correct file name, location, and any required frontmatter format.
- **Prompt improvements** — If the core `chat2goal` prompt can be more effective, open a PR with a before/after example showing the improvement.

## Adding a New Platform

1. Research the platform's required file name, location, and frontmatter (if any).
2. Add an entry to the `PACKAGES` dict in `build.py`:
   ```python
   "chat2goal-yourplatform": {
       "readme": README_YOURPLATFORM,
       "files": {
           "correct_filename.ext": STANDARD_CONTENT,
       },
       "scripts": None,
   },
   ```
3. Write a focused `README_YOURPLATFORM` string with only that platform's install steps.
4. Run `python build.py` and verify the zip contents look correct.
5. Open a PR with the updated `build.py` and a note on how you verified the install.

## Versioning

Versions follow `MAJOR.MINOR.PATCH`:
- `PATCH` — prompt text fixes, README corrections
- `MINOR` — new platform added, new install script
- `MAJOR` — breaking change to the prompt structure or output format

Update `VERSION = "x.y.z"` at the top of `build.py` before opening a release PR.

## License

By contributing, you agree your contributions are licensed under [Apache 2.0](LICENSE).
