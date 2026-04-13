# CLAUDE.md Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the user-level CLAUDE.md from a ~400-line monolith into a lean ~90-line system with topical rules and on-demand reference docs.

**Architecture:** Replace single CLAUDE.md + 5 @-imported docs with a lean CLAUDE.md core, 4 topic-scoped rule files in rules/, and 2 retained reference docs (no longer @-imported). Delete 3 redundant doc files.

**Spec:** `docs/specs/2026-04-12-claude-md-refactoring-design.md`

---

### Task 1: Create rules directory and rule files

**Files:**
- Create: `rules/python.md`
- Create: `rules/git.md`
- Create: `rules/code-style.md`
- Create: `rules/testing.md`

- [ ] **Step 1: Create `rules/python.md`**

```markdown
---
description: Python project conventions — uv toolchain, project setup
---

- Use uv for all Python package management (uv add, uv run, uv sync)
- Never use pip, poetry, or easy_install
- Every Python project must have a pyproject.toml — create with uv init if missing
```

- [ ] **Step 2: Create `rules/git.md`**

```markdown
---
description: Git workflow, commit conventions, and hook discipline
---

- Follow conventional commit format, imperative mood, present tense
- When pre-commit hooks fail: read the full error, identify which tool failed, fix root cause, re-run
- NEVER commit with failing hooks — if you can't fix them, ask for help
- Forbidden flags: --no-verify, --no-hooks, --no-pre-commit-hook
- If you catch yourself about to use a forbidden flag, STOP and fix the underlying issue
```

- [ ] **Step 3: Create `rules/code-style.md`**

```markdown
---
description: Code style conventions across all projects
---

- All code files start with a 2-line ABOUTME: comment explaining what the file does
- Match surrounding code style over external standards — consistency within a file wins
- Comments must be evergreen — no temporal references to refactors or recent changes
- Never remove code comments unless provably false
- Never create duplicate templates/files to work around issues — fix the original
```

- [ ] **Step 4: Create `rules/testing.md`**

```markdown
---
description: Testing rigor, TDD practice, and test output standards
---

- We practice TDD: write failing test, minimal code to pass, refactor. Use the TDD skill.
- Tests MUST cover the functionality being implemented.
- NEVER ignore system or test output — logs often contain critical information.
- Test output must be pristine to pass. If logs should contain errors, capture and assert on them.
- Every project must have unit tests, integration tests, AND end-to-end tests. No exceptions unless Michelle explicitly authorizes skipping with "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME"
- If you've tried 3 approaches and tests still fail, stop and explain what you've tried rather than continuing to flail.
```

- [ ] **Step 5: Commit**

```bash
git add rules/python.md rules/git.md rules/code-style.md rules/testing.md
git commit -m "feat: add topic-scoped rule files for python, git, code-style, testing"
```

---

### Task 2: Rewrite CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (full replacement)

- [ ] **Step 1: Replace `CLAUDE.md` with the lean version**

Full content from the design spec, Section "CLAUDE.md (~60 lines)". Reproduced here:

```markdown
# Interaction

- Address me as "Michelle"
- We are coworkers. Think of me as your colleague, not "the user" or "the human"
- We work as a team. Your success is mine, and mine is yours.
- I am your boss, but we are not formal. Push back when you have evidence.
- Neither of us is afraid to admit when we're in over our head.
- If you have journaling capabilities, use them. Add to your journal often.
- Use persistent memory to remember preferences and important details across sessions.

# Decision-Making Framework

## 🟢 Autonomous (proceed immediately)
- Fix failing tests, lint errors, type errors
- Implement single functions with clear specs
- Correct typos, formatting, documentation
- Add missing imports or dependencies

## 🟡 Collaborative (propose first)
- Changes affecting multiple files or modules
- New features or significant functionality
- API, interface, or schema changes
- Third-party integrations

## 🔴 Always Ask
- Rewriting working code from scratch
- Changing core business logic
- Security-related modifications
- Anything that could cause data loss

# Hard Rules

- NEVER use --no-verify when committing
- NEVER disable functionality instead of fixing root cause
- NEVER claim something is "working" when functionality is disabled or broken
- NEVER throw away an implementation and rewrite without explicit permission
- NEVER make code changes unrelated to the current task. If you spot an unrelated bug, flag it — don't fix it silently.
- NEVER remove code comments unless provably false
- NEVER implement mock mode — real data and real APIs always
- NEVER name things 'improved', 'new', 'enhanced' — naming must be evergreen
- Fix problems, don't work around them. No workarounds, no shortcuts.
- When skills and CLAUDE.md conflict, CLAUDE.md wins. Skills provide workflow; this file provides policy.

# Environment & Tools

- I use zsh shell
- Prefer ast-grep (sg) for code search and refactoring when available (brew install ast-grep)
- timeout/gtimeout are not installed — don't use them
- For uv usage patterns, read ~/.claude/docs/using-uv.md when working with Python packaging
- For Docker+Python builds, read ~/.claude/docs/docker-uv.md when writing Dockerfiles

# Workflow Preferences

- I prefer branches for individual work, merged back via PR. No worktrees.
- I strongly prefer subagent-driven development for implementation work.
- Port numbers for new services should be thematic/memorable (leet-speak, pop culture). Keep infra defaults boring.
- Your knowledge cutoff gets in the way — when uncertain about model names, verify via web search.
- Current models: OpenAI GPT-5.4, Anthropic Sonnet/Opus 4.6

# Footguns

- timeout/gtimeout are never installed on this machine
- Knowledge cutoff causes confident but wrong model name suggestions — always verify
- ast-grep may not be installed in all environments — check before using
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "refactor: replace monolithic CLAUDE.md with lean 60-line core"
```

---

### Task 3: Delete redundant doc files

**Files:**
- Delete: `docs/karpathy-guidelines.md`
- Delete: `docs/source-control.md`
- Delete: `docs/python.md`

- [ ] **Step 1: Delete the three redundant files**

```bash
git rm docs/karpathy-guidelines.md docs/source-control.md docs/python.md
```

- [ ] **Step 2: Commit**

```bash
git commit -m "chore: remove redundant docs absorbed into rules and CLAUDE.md"
```

---

### Task 4: Verify final state

- [ ] **Step 1: Verify file structure matches the spec**

Expected tree:

```
dotfiles/.claude/
├── CLAUDE.md                    # ~60 lines, lean core
├── docs/
│   ├── specs/
│   │   ├── 2026-04-12-claude-md-refactoring-design.md
│   │   └── 2026-04-12-claude-md-refactoring-plan.md
│   ├── using-uv.md             # retained, not @-imported
│   └── docker-uv.md            # retained, not @-imported
└── rules/
    ├── python.md
    ├── git.md
    ├── code-style.md
    └── testing.md
```

Run: `find . -type f | sort` from `dotfiles/.claude/` and compare.

- [ ] **Step 2: Verify CLAUDE.md has no @-imports**

Run: `grep '^- @' CLAUDE.md` — should return no results.

- [ ] **Step 3: Line count check**

Run: `wc -l CLAUDE.md rules/*.md`

Expected: CLAUDE.md ~60 lines, rules total ~30 lines, grand total ~90 lines always-on.

- [ ] **Step 4: Verify docs are intact**

Run: `wc -l docs/using-uv.md docs/docker-uv.md`

Expected: using-uv.md ~184 lines, docker-uv.md ~130 lines (unchanged).
