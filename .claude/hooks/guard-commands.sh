#!/usr/bin/env bash
# ABOUTME: PreToolUse hook — blocks Bash commands that violate CLAUDE.md/rules policy
# ABOUTME: (git hook-bypass flags, pip/poetry/easy_install, uninstalled timeout). Fails open.

set -u

usage() {
  cat <<'EOF'
guard-commands.sh — Claude Code PreToolUse hook (Bash)

Reads a PreToolUse JSON payload on stdin and inspects .tool_input.command.
Blocks (exit 2, reason on stderr) when the command would violate policy:
  - git hook-bypass flags: --no-verify, --no-hooks, --no-pre-commit-hook
  - pip / pip3 / python -m pip / easy_install / poetry  (use uv instead)
  - timeout / gtimeout  (not installed on this machine)
Anything else, or any parse error, exits 0 (fail open — never blocks real work).

Register in ~/.claude/settings.json (intentionally NOT tracked by yadm — it holds
machine-local config). Merge this into the top-level object, then restart Claude Code:

  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "$HOME/.claude/hooks/guard-commands.sh" } ] } ]
  }
EOF
}

case "${1:-}" in
  -h | --help) usage; exit 0 ;;
esac

# Fail open: if stdin isn't a payload (e.g. a TTY), do nothing.
[ -t 0 ] && exit 0

payload="$(cat)"
tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null)"
cmd="$(printf '%s' "$payload"  | jq -r '.tool_input.command // empty' 2>/dev/null)"

# Only inspect Bash; fail open on anything unparseable or empty.
[ "$tool" = "Bash" ] || exit 0
[ -n "$cmd" ] || exit 0

block() {
  printf 'Blocked by guard-commands hook: %s\n' "$1" >&2
  exit 2
}

# A command starts a "statement" at string start or right after ; & | ( — this lets us
# match real invocations (`pip install`) while ignoring substrings (`-m "pip install"`).
STMT='(^|[;&|(])[[:space:]]*(sudo[[:space:]]+)?'

# 1. git hook-bypass flags
if printf '%s' "$cmd" | grep -Eq 'git[[:space:]]' \
  && printf '%s' "$cmd" | grep -Eq -- '--no-verify|--no-hooks|--no-pre-commit-hook'; then
  block "git hook-bypass flags are forbidden (--no-verify/--no-hooks). Fix the failing hook, don't skip it. See rules/git.md."
fi

# 2. pip / poetry / easy_install — uv is the only sanctioned package manager (uv pip is fine).
if printf '%s' "$cmd" | grep -Eq "${STMT}pip3?[[:space:]]+install" \
  || printf '%s' "$cmd" | grep -Eq -- '-m[[:space:]]+pip[[:space:]]+install' \
  || printf '%s' "$cmd" | grep -Eq "${STMT}easy_install([[:space:]]|\$)" \
  || printf '%s' "$cmd" | grep -Eq "${STMT}poetry[[:space:]]+(add|install|remove|update|lock)"; then
  block "Use uv (uv add / uv run / uv sync) — pip/poetry/easy_install are not allowed. See rules/python.md."
fi

# 3. timeout/gtimeout — not installed here; block early with guidance instead of a cryptic failure.
if printf '%s' "$cmd" | grep -Eq "${STMT}g?timeout[[:space:]]"; then
  block "timeout/gtimeout aren't installed on this machine — run the command directly without them."
fi

exit 0
