---
description: Git workflow, commit conventions, and hook discipline
---

- Follow conventional commit format, imperative mood, present tense
- When pre-commit hooks fail: read the full error, identify which tool failed, fix root cause, re-run
- NEVER commit with failing hooks — if you can't fix them, ask for help
- Forbidden flags: --no-verify, --no-hooks, --no-pre-commit-hook
- If you catch yourself about to use a forbidden flag, STOP and fix the underlying issue
