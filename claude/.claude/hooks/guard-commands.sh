#!/usr/bin/env bash
# ABOUTME: PreToolUse hook — blocks Bash commands that violate CLAUDE.md policy
# ABOUTME: (git hook-bypass flags and core.hooksPath overrides, pip/poetry/easy_install). Fails open.

set -u

usage() {
  cat <<'EOF'
guard-commands.sh — Claude Code PreToolUse hook (Bash)

Reads a PreToolUse JSON payload on stdin and inspects .tool_input.command.
Blocks (exit 2, reason on stderr) when the command would violate policy:
  - git hook-bypass flags: --no-verify, --no-hooks, --no-pre-commit-hook,
    and -n on git commit (alone or bundled, e.g. -nm, -an)
  - overriding core.hooksPath: git -c / --config-env, or git config setting it
  - pip / pip3 / python -m pip / easy_install / poetry  (use uv instead)
Anything else, or any parse error, exits 0 (fail open — never blocks real work).

The dotfiles' ./install registers this hook in ~/.claude/settings.json, adding
this entry (with $HOME expanded) unless one already points at the hook. The file
itself stays untracked because Claude Code rewrites it. Restart Claude Code after.

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

# 1. git hook-bypass flags. git accepts unambiguous prefixes of long options, so --no-veri and
# --no-verif also mean --no-verify; shorter ones clash with --no-verbose and git rejects them.
if printf '%s' "$cmd" | grep -Eq 'git[[:space:]]' \
  && printf '%s' "$cmd" | grep -Eq -- '--no-veri|--no-hooks|--no-pre-commit-hook'; then
  block "git hook-bypass flags are forbidden (--no-verify/--no-hooks). Fix the failing hook, don't skip it. See 'Version control' in CLAUDE.md."
fi

# 2. pip / poetry / easy_install — uv is the only sanctioned package manager (uv pip is fine).
if printf '%s' "$cmd" | grep -Eq "${STMT}pip3?[[:space:]]+install" \
  || printf '%s' "$cmd" | grep -Eq -- '-m[[:space:]]+pip[[:space:]]+install' \
  || printf '%s' "$cmd" | grep -Eq "${STMT}easy_install([[:space:]]|\$)" \
  || printf '%s' "$cmd" | grep -Eq "${STMT}poetry[[:space:]]+(add|install|remove|update|lock)"; then
  block "Use uv (uv add / uv run / uv sync) — pip/poetry/easy_install are not allowed. See 'Languages & tools' in CLAUDE.md."
fi

# 3. git commit -n — short for --no-verify, but only on commit (log -n, clean -n, push -n differ).
# Quoted strings are dropped first so a message like -m "fix -n handling" doesn't match. Bundled
# flags count (-nm, -an) until a letter that takes a value (m F c C t S u): -mnote and -uno pass.
unquoted="$(printf '%s' "$cmd" | sed -e 's/"[^"]*"//g' -e "s/'[^']*'//g")"
if printf '%s' "$unquoted" \
  | grep -Eq '(^|[^[:alnum:]_-])git[[:space:]]+([^;&|]*[[:space:]])?commit([[:space:]][^;&|]*)?[[:space:]]-[^[:space:]mFcCtSu=-]*n'; then
  block "git commit -n is --no-verify, which is forbidden. Fix the failing hook, don't skip it. See 'Version control' in CLAUDE.md."
fi

# 4. core.hooksPath — pointing it elsewhere skips every hook. Config keys are case-insensitive,
# hence grep -i. Reading it (git config --get/get core.hooksPath, no value) stays allowed;
# redirects (2>/dev/null, >&2) are dropped first so they don't pass for a value.
unredirected="$(printf '%s' "$cmd" | sed -E 's/[0-9]*[<>]+&?[^[:space:];&|]*//g')"
if printf '%s' "$cmd" \
  | grep -Eiq "git[[:space:]]+([^;&|]*[[:space:]])?(-c[[:space:]]*|--config-env[=[:space:]])['\"]?core\.hookspath=" \
  || printf '%s' "$unredirected" \
  | grep -Eiq "git[[:space:]]+([^;&|]*[[:space:]])?config[[:space:]]+([^;&|]*[[:space:]])?['\"]?core\.hookspath['\"]?[[:space:]]+['\"]?[^-;&|[:space:]]"; then
  block "overriding core.hooksPath skips git hooks, which is forbidden. Fix the failing hook instead. See 'Version control' in CLAUDE.md."
fi

exit 0
