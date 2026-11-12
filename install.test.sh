#!/usr/bin/env bash
# ABOUTME: Tests for install — runs it against scratch lists with stub omarchy, brew, claude and
# ABOUTME: uname, and real stow into a scratch HOME. Run: ./install.test.sh (nonzero if any fail).

set -u
REPO="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
pass=0
fail=0

# The real omarchy sits in /usr/bin and /usr/share/omarchy/bin, so tests never put system
# dirs on PATH: it holds only the stubs and $TOOLS (symlinks to what install needs), and
# bash runs by absolute path. No test can reach the real omarchy or install anything.
# The same PATH keeps the real claude out of reach, so no test installs a plugin or
# registers an MCP server.
# stow is real; every run sets HOME to a scratch dir, so it only links into that.
# jq is real too and only ever edits $SANDBOX/home/.claude/settings.json.
# NOSTOW is TOOLS without stow; NOJQ is TOOLS without jq.
# uname is a stub that prints $STUB_OS (default Linux), so the suite covers both the
# Omarchy and the macOS path whichever system it runs on.
TOOLS="$SCRATCH/tools"
NOSTOW="$SCRATCH/nostow"
NOJQ="$SCRATCH/nojq"
mkdir -p "$TOOLS" "$NOSTOW" "$NOJQ"
for tool in dirname cat cp mv rm; do
  ln -s "$(command -v "$tool")" "$TOOLS/$tool"
  ln -s "$(command -v "$tool")" "$NOSTOW/$tool"
  ln -s "$(command -v "$tool")" "$NOJQ/$tool"
done
for dir in "$TOOLS" "$NOSTOW" "$NOJQ"; do
  cat >"$dir/uname" <<EOF
#!$BASH
printf '%s\n' "\${STUB_OS:-Linux}"
EOF
  chmod +x "$dir/uname"
done
ln -s "$(command -v stow)" "$TOOLS/stow"
ln -s "$(command -v stow)" "$NOJQ/stow"
ln -s "$(command -v jq)" "$TOOLS/jq"
ln -s "$(command -v jq)" "$NOSTOW/jq"

ok() { pass=$((pass + 1)); }
not_ok() {
  fail=$((fail + 1))
  printf 'FAIL: %s\n' "$1"
  shift
  [ $# -gt 0 ] && printf '      %s\n' "$@"
}

# setup <arch-list-contents> <aur-list-contents> — fresh sandbox with a copy of install,
# the given lists, a comment-only claude-plugins.txt and claude-mcp.txt, a copy of the
# claude stow package, a repo-only .claude/plans file, an empty $SANDBOX/home to stow into,
# a stub omarchy that appends "$*" to $SANDBOX/calls and exits $STUB_EXIT, and a stub claude
# that appends "$*" to $SANDBOX/claude-calls and exits $STUB_CLAUDE_EXIT — except for
# `mcp get`, which exits $STUB_MCP_GET_EXIT (default 1: no server has that name).
setup() {
  SANDBOX="$(mktemp -d "$SCRATCH/case.XXXXXX")"
  cp "$REPO/install" "$SANDBOX/install"
  cp -R "$REPO/claude" "$SANDBOX/claude"
  mkdir -p "$SANDBOX/packages" "$SANDBOX/bin" "$SANDBOX/home" "$SANDBOX/.claude/plans"
  printf 'plan\n' >"$SANDBOX/.claude/plans/plan.md"
  printf '%s' "$1" >"$SANDBOX/packages/arch.txt"
  printf '%s' "$2" >"$SANDBOX/packages/aur.txt"
  printf '# no plugins\n' >"$SANDBOX/packages/claude-plugins.txt"
  printf '# no servers\n' >"$SANDBOX/packages/claude-mcp.txt"
  cat >"$SANDBOX/bin/omarchy" <<EOF
#!$BASH
printf '%s\n' "\$*" >>"$SANDBOX/calls"
exit "\${STUB_EXIT:-0}"
EOF
  chmod +x "$SANDBOX/bin/omarchy"
  cat >"$SANDBOX/bin/claude" <<EOF
#!$BASH
printf '%s\n' "\$*" >>"$SANDBOX/claude-calls"
case "\$1 \$2" in
  'mcp get') exit "\${STUB_MCP_GET_EXIT:-1}" ;;
esac
exit "\${STUB_CLAUDE_EXIT:-0}"
EOF
  chmod +x "$SANDBOX/bin/claude"
  : >"$SANDBOX/calls"
  : >"$SANDBOX/claude-calls"
}

# setup_mac <brew-list-contents> <cask-list-contents> — like setup, but for the macOS path:
# no arch/aur lists and no omarchy; instead packages/brew.txt, packages/cask.txt and a stub
# brew that appends "brew $*" to $SANDBOX/calls and exits $STUB_EXIT. Run install after it
# with STUB_OS=Darwin.
setup_mac() {
  setup '' ''
  rm "$SANDBOX/packages/arch.txt" "$SANDBOX/packages/aur.txt" "$SANDBOX/bin/omarchy"
  printf '%s' "$1" >"$SANDBOX/packages/brew.txt"
  printf '%s' "$2" >"$SANDBOX/packages/cask.txt"
  cat >"$SANDBOX/bin/brew" <<EOF
#!$BASH
printf 'brew %s\n' "\$*" >>"$SANDBOX/calls"
exit "\${STUB_EXIT:-0}"
EOF
  chmod +x "$SANDBOX/bin/brew"
}

# write_plugin_list <contents> — replaces the sandbox's comment-only claude-plugins.txt.
write_plugin_list() { printf '%s' "$1" >"$SANDBOX/packages/claude-plugins.txt"; }

# write_mcp_list <contents> — replaces the sandbox's comment-only claude-mcp.txt.
write_mcp_list() { printf '%s' "$1" >"$SANDBOX/packages/claude-mcp.txt"; }

# stub_command <name> — puts a do-nothing <name> on the sandbox's PATH, standing in for an
# MCP server's command that is installed.
stub_command() {
  printf '#!%s\n' "$BASH" >"$SANDBOX/bin/$1"
  chmod +x "$SANDBOX/bin/$1"
}

# file_mode <file> — prints the octal permission bits (GNU stat, else BSD stat).
file_mode() { stat -c %a "$1" 2>/dev/null || stat -f %Lp "$1"; }

# run_install [args...] — runs the sandbox copy with the stubs first on PATH and HOME set
# to $SANDBOX/home; sets $status, $out and $err.
run_install() {
  HOME="$SANDBOX/home" PATH="$SANDBOX/bin:$TOOLS" "$BASH" "$SANDBOX/install" "$@" \
    >"$SANDBOX/out" 2>"$SANDBOX/err"
  status=$?
  out="$(cat "$SANDBOX/out")"
  err="$(cat "$SANDBOX/err")"
}

# expect_calls <description> <expected calls file contents>
expect_calls() {
  local got
  got="$(cat "$SANDBOX/calls")"
  if [ "$got" = "$2" ]; then ok; else not_ok "$1" "expected calls: $(printf '%q' "$2")" "got calls:      $(printf '%q' "$got")"; fi
}

# expect_claude_calls <description> <expected claude-calls file contents>
expect_claude_calls() {
  local got
  got="$(cat "$SANDBOX/claude-calls")"
  if [ "$got" = "$2" ]; then ok; else not_ok "$1" "expected claude calls: $(printf '%q' "$2")" "got claude calls:      $(printf '%q' "$got")"; fi
}

expect_status() {
  if [ "$status" = "$2" ]; then ok; else not_ok "$1" "expected exit $2, got $status" "stderr: $err"; fi
}

expect_err_contains() {
  case "$err" in
    *"$2"*) ok ;;
    *) not_ok "$1" "expected stderr to contain: $2" "stderr: $err" ;;
  esac
}

# --- parsing: comments, blank lines, trailing comments, whitespace ---
setup $'# header comment\n\ngit\n   \n  tmux  \njq # needed by the hook\n\t# indented comment\nstow\t\n' ''
run_install
expect_status "parses arch list" 0
expect_calls "skips comments/blanks, trims whitespace and trailing comments" 'pkg add git tmux jq stow'

# --- last line without a trailing newline still counts ---
setup $'git\njq' ''
run_install
expect_calls "reads a final line with no newline" 'pkg add git jq'

# --- AUR list gets its own call ---
setup $'git\n' $'# aur\nfoo-bin # comment\n  bar-git\n'
run_install
expect_status "arch and aur lists" 0
expect_calls "calls pkg add then pkg aur add" $'pkg add git\npkg aur add foo-bin bar-git'

# --- empty (comments only) AUR list means no aur call ---
setup $'git\n' $'# nothing here yet\n\n'
run_install
expect_calls "comment-only aur list skips the aur call" 'pkg add git'

# --- empty arch list means no arch call ---
setup $'# nothing\n' $'foo-bin\n'
run_install
expect_status "empty arch list" 0
expect_calls "comment-only arch list skips the arch call" 'pkg aur add foo-bin'

# --- the real repo lists feed the real package names ---
setup '' ''
cp "$REPO/packages/arch.txt" "$REPO/packages/aur.txt" "$SANDBOX/packages/"
run_install
expect_status "repo lists" 0
expect_calls "repo arch.txt passes decision 8's packages; aur.txt is empty" \
  'pkg add aws-cli-v2 duckdb uv bitwarden tmux ghostty git ast-grep stow jq shellcheck'

# --- omarchy missing from PATH ---
setup $'git\n' ''
HOME="$SANDBOX/home" PATH="$TOOLS" "$BASH" "$SANDBOX/install" >"$SANDBOX/out" 2>"$SANDBOX/err"
status=$?
err="$(cat "$SANDBOX/err")"
expect_status "missing omarchy exits nonzero" 1
expect_err_contains "missing omarchy names omarchy" "omarchy"

# --- missing list files ---
setup $'git\n' ''
rm "$SANDBOX/packages/arch.txt"
run_install
expect_status "missing arch.txt exits nonzero" 1
expect_err_contains "missing arch.txt names the file" "packages/arch.txt"
expect_calls "missing arch.txt makes no omarchy calls" ''

setup $'git\n' ''
rm "$SANDBOX/packages/aur.txt"
run_install
expect_status "missing aur.txt exits nonzero" 1
expect_err_contains "missing aur.txt names the file" "packages/aur.txt"
expect_calls "missing aur.txt makes no omarchy calls" ''

# In the next two the other claude list has an entry, so "no claude calls" can only mean
# the missing list stopped the run before either step.
setup $'git\n' ''
write_mcp_list $'notes notes-server\n'
stub_command notes-server
rm "$SANDBOX/packages/claude-plugins.txt"
run_install
expect_status "missing claude-plugins.txt exits nonzero" 1
expect_err_contains "missing claude-plugins.txt names the file" "packages/claude-plugins.txt"
expect_calls "missing claude-plugins.txt makes no omarchy calls" ''
expect_claude_calls "missing claude-plugins.txt makes no claude calls" ''

setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\n'
rm "$SANDBOX/packages/claude-mcp.txt"
run_install
expect_status "missing claude-mcp.txt exits nonzero" 1
expect_err_contains "missing claude-mcp.txt names the file" "packages/claude-mcp.txt"
expect_calls "missing claude-mcp.txt makes no omarchy calls" ''
expect_claude_calls "missing claude-mcp.txt makes no claude calls" ''

# --- omarchy failure propagates, naming the list ---
setup $'git\n' $'foo-bin\n'
STUB_EXIT=1 run_install
expect_status "failing omarchy exits nonzero" 1
expect_err_contains "failure names the arch list" "arch.txt"
expect_calls "stops after the arch failure" 'pkg add git'

setup '' $'foo-bin\n'
STUB_EXIT=1 run_install
expect_status "failing aur call exits nonzero" 1
expect_err_contains "failure names the aur list" "aur.txt"

# --- macOS: brew.txt goes to `brew install`, cask.txt to `brew install --cask` ---
setup_mac $'# formulae\ngit\n  stow  \njq # needed by the hook\n' $'# casks\nghostty\nbitwarden'
STUB_OS=Darwin run_install
expect_status "macOS: brew and cask lists" 0
expect_calls "macOS: calls brew install then brew install --cask" \
  $'brew install git stow jq\nbrew install --cask ghostty bitwarden'

# --- macOS: a comment-only list is skipped ---
setup_mac $'git\n' $'# no casks\n'
STUB_OS=Darwin run_install
expect_status "macOS: empty cask list" 0
expect_calls "macOS: comment-only cask list skips the cask call" 'brew install git'

# --- macOS: the real repo lists feed the real package names ---
setup_mac '' ''
cp "$REPO/packages/brew.txt" "$REPO/packages/cask.txt" "$SANDBOX/packages/"
STUB_OS=Darwin run_install
expect_status "macOS: repo lists" 0
expect_calls "macOS: repo brew.txt and cask.txt pass their packages" \
  $'brew install awscli duckdb uv tmux git ast-grep stow jq shellcheck gh 2389-research/tap/pulse\nbrew install --cask bitwarden ghostty'

# --- macOS: never needs omarchy or the Arch lists, and stows and registers the hook ---
setup_mac $'git\n' ''
STUB_OS=Darwin run_install
expect_status "macOS: runs without omarchy, arch.txt or aur.txt" 0
if [ -L "$SANDBOX/home/.claude/CLAUDE.md" ]; then ok; else not_ok "macOS: stows CLAUDE.md"; fi
if jq -e '.hooks.PreToolUse[0].matcher == "Bash"' "$SANDBOX/home/.claude/settings.json" >/dev/null 2>&1; then
  ok
else
  not_ok "macOS: registers the guard hook"
fi

# --- macOS: the steps after the hook run too ---
setup_mac $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\n'
STUB_OS=Darwin run_install
expect_status "macOS: local.md and plugins" 0
if [ -f "$SANDBOX/home/.claude/local.md" ]; then ok; else not_ok "macOS: creates local.md"; fi
expect_claude_calls "macOS: installs the plugins" \
  'plugin install superpowers --marketplace anthropics/claude-plugins-official --scope user'

setup_mac $'git\n' ''
write_mcp_list $'notes notes-server --stdio\n'
stub_command notes-server
STUB_OS=Darwin run_install
expect_status "macOS: MCP servers" 0
expect_claude_calls "macOS: registers the MCP servers" \
  $'mcp get notes\nmcp add --scope user notes -- notes-server --stdio'

# --- macOS: brew missing from PATH ---
setup_mac $'git\n' ''
rm "$SANDBOX/bin/brew"
STUB_OS=Darwin run_install
expect_status "macOS: missing brew exits nonzero" 1
expect_err_contains "macOS: missing brew names brew" "brew not found"

# --- macOS: missing list files ---
setup_mac $'git\n' ''
rm "$SANDBOX/packages/brew.txt"
STUB_OS=Darwin run_install
expect_status "macOS: missing brew.txt exits nonzero" 1
expect_err_contains "macOS: missing brew.txt names the file" "packages/brew.txt"
expect_calls "macOS: missing brew.txt makes no brew calls" ''

setup_mac $'git\n' ''
rm "$SANDBOX/packages/cask.txt"
STUB_OS=Darwin run_install
expect_status "macOS: missing cask.txt exits nonzero" 1
expect_err_contains "macOS: missing cask.txt names the file" "packages/cask.txt"
expect_calls "macOS: missing cask.txt makes no brew calls" ''

setup_mac $'git\n' ''
rm "$SANDBOX/packages/claude-plugins.txt"
STUB_OS=Darwin run_install
expect_status "macOS: missing claude-plugins.txt exits nonzero" 1
expect_err_contains "macOS: missing claude-plugins.txt names the file" "packages/claude-plugins.txt"
expect_calls "macOS: missing claude-plugins.txt makes no brew calls" ''

setup_mac $'git\n' ''
rm "$SANDBOX/packages/claude-mcp.txt"
STUB_OS=Darwin run_install
expect_status "macOS: missing claude-mcp.txt exits nonzero" 1
expect_err_contains "macOS: missing claude-mcp.txt names the file" "packages/claude-mcp.txt"
expect_calls "macOS: missing claude-mcp.txt makes no brew calls" ''

# --- macOS: brew failure propagates, naming the list ---
setup_mac $'git\n' $'ghostty\n'
STUB_OS=Darwin STUB_EXIT=1 run_install
expect_status "macOS: failing brew exits nonzero" 1
expect_err_contains "macOS: failure names the brew list" "brew.txt"
expect_calls "macOS: stops after the brew failure" 'brew install git'

# --- macOS: a missing stow points at brew.txt ---
setup_mac $'git\n' ''
HOME="$SANDBOX/home" PATH="$SANDBOX/bin:$NOSTOW" STUB_OS=Darwin "$BASH" "$SANDBOX/install" >"$SANDBOX/out" 2>"$SANDBOX/err"
status=$?
err="$(cat "$SANDBOX/err")"
expect_status "macOS: missing stow exits nonzero" 1
expect_err_contains "macOS: missing stow points at brew.txt" "packages/brew.txt"

# --- any other system is refused before anything runs ---
setup $'git\n' ''
STUB_OS=FreeBSD run_install
expect_status "unsupported system exits nonzero" 1
expect_err_contains "unsupported system names it" "FreeBSD"
expect_calls "unsupported system makes no package calls" ''
if [ ! -e "$SANDBOX/home/.claude" ]; then ok; else not_ok "unsupported system stows nothing"; fi

# expect_link <description> <path under $SANDBOX/home> — passes if the path is a symlink
# that resolves to the same path in the sandbox's claude package.
expect_link() {
  local link="$SANDBOX/home/$2" want="$SANDBOX/claude/$2"
  if [ -L "$link" ] && [ "$(readlink -f "$link")" = "$(readlink -f "$want")" ]; then
    ok
  else
    not_ok "$1" "expected $link to link to $want"
  fi
}

# --- stow: a clean HOME gets links into the claude package ---
setup $'git\n' ''
run_install
expect_status "stow into a clean home" 0
expect_link "stows CLAUDE.md" .claude/CLAUDE.md
expect_link "stows the guard hook" .claude/hooks/guard-commands.sh
# No folding: ~/.claude stays a real dir, so Claude Code's own files never land in the repo.
if [ -d "$SANDBOX/home/.claude" ] && [ ! -L "$SANDBOX/home/.claude" ] \
  && [ -d "$SANDBOX/home/.claude/hooks" ] && [ ! -L "$SANDBOX/home/.claude/hooks" ]; then
  ok
else
  not_ok "HOME/.claude and HOME/.claude/hooks are real dirs, not links into the repo"
fi
if [ ! -e "$SANDBOX/home/.claude/plans" ]; then ok; else not_ok ".claude/plans is never stowed"; fi

# --- stow: re-running on a stowed HOME is a no-op ---
run_install
expect_status "re-run on a stowed home" 0
expect_link "re-run keeps the CLAUDE.md link" .claude/CLAUDE.md

# --- stow: a skill is linked file by file, next to the skills Claude Code keeps there itself ---
setup $'git\n' ''
mkdir -p "$SANDBOX/home/.claude/skills/synced"
printf 'written by Claude Code\n' >"$SANDBOX/home/.claude/skills/synced/keep.txt"
cp "$SANDBOX/home/.claude/skills/synced/keep.txt" "$SANDBOX/before-keep.txt"
run_install
expect_status "stow next to Claude Code's own skills" 0
expect_link "stows the uv skill" .claude/skills/uv/SKILL.md
if [ -d "$SANDBOX/home/.claude/skills" ] && [ ! -L "$SANDBOX/home/.claude/skills" ] \
  && [ -d "$SANDBOX/home/.claude/skills/uv" ] && [ ! -L "$SANDBOX/home/.claude/skills/uv" ]; then
  ok
else
  not_ok "HOME/.claude/skills and HOME/.claude/skills/uv are real dirs, not links into the repo"
fi
if [ ! -L "$SANDBOX/home/.claude/skills/synced/keep.txt" ] \
  && cmp -s "$SANDBOX/before-keep.txt" "$SANDBOX/home/.claude/skills/synced/keep.txt"; then
  ok
else
  not_ok "Claude Code's own skill file is untouched"
fi

# --- stow: a real file in the way stops the run and stays untouched ---
setup $'git\n' ''
mkdir -p "$SANDBOX/home/.claude"
printf 'my own\nCLAUDE.md\n' >"$SANDBOX/home/.claude/CLAUDE.md"
run_install
expect_status "conflicting CLAUDE.md exits nonzero" 1
expect_err_contains "conflict shows stow's message" ".claude/CLAUDE.md"
expect_err_contains "conflict says to move the file aside" "move"
if [ "$(cat "$SANDBOX/home/.claude/CLAUDE.md")" = $'my own\nCLAUDE.md' ] \
  && [ ! -L "$SANDBOX/home/.claude/CLAUDE.md" ]; then
  ok
else
  not_ok "conflicting CLAUDE.md keeps its contents"
fi
created="$(cd "$SANDBOX/home" && find . -mindepth 1 | sort | tr '\n' ' ')"
if [ "$created" = "./.claude ./.claude/CLAUDE.md " ]; then ok; else not_ok "conflict creates nothing" "home holds: $created"; fi

# --- stow missing from PATH (after the package step, which installs it) ---
setup $'git\n' ''
HOME="$SANDBOX/home" PATH="$SANDBOX/bin:$NOSTOW" "$BASH" "$SANDBOX/install" >"$SANDBOX/out" 2>"$SANDBOX/err"
status=$?
err="$(cat "$SANDBOX/err")"
expect_status "missing stow exits nonzero" 1
expect_err_contains "missing stow names stow" "stow not found"
expect_calls "missing stow still runs the package step first" 'pkg add git'

# --- settings.json: the guard hook gets registered ---
# settings_file / hook_path — the sandbox's ~/.claude/settings.json and the hook path
# install should register (absolute, $HOME already expanded).
settings_file() { printf '%s' "$SANDBOX/home/.claude/settings.json"; }
hook_path() { printf '%s' "$SANDBOX/home/.claude/hooks/guard-commands.sh"; }

# expect_settings <description> <expected JSON> — compares key-sorted, compact forms.
expect_settings() {
  local got want
  got="$(jq -S -c . "$(settings_file)" 2>&1)"
  want="$(printf '%s' "$2" | jq -S -c .)"
  if [ "$got" = "$want" ]; then ok; else not_ok "$1" "expected: $want" "got:      $got"; fi
}

# expect_unchanged <description> <copy of the original file>
expect_unchanged() {
  if cmp -s "$2" "$(settings_file)"; then ok; else not_ok "$1" "settings.json changed: $(cat "$(settings_file)")"; fi
}

# expect_no_temp <description> — nothing but settings.json itself matches settings.json*.
expect_no_temp() {
  local leftover
  leftover="$(cd "$SANDBOX/home/.claude" && find . -maxdepth 1 -name 'settings.json?*')"
  if [ -z "$leftover" ]; then ok; else not_ok "$1" "found: $leftover"; fi
}

# --- a missing settings.json is created holding just the hook ---
setup $'git\n' ''
run_install
expect_status "creates settings.json" 0
expect_settings "new settings.json holds just the hook" \
  "{\"hooks\":{\"PreToolUse\":[{\"matcher\":\"Bash\",\"hooks\":[{\"type\":\"command\",\"command\":\"$(hook_path)\"}]}]}}"

# --- re-running leaves the registered file byte-identical ---
cp "$(settings_file)" "$SANDBOX/before.json"
run_install
expect_status "re-run with the hook registered" 0
expect_unchanged "re-run leaves settings.json byte-identical" "$SANDBOX/before.json"

# --- existing keys and hooks are preserved; the hook is appended ---
setup $'git\n' ''
mkdir -p "$SANDBOX/home/.claude"
cat >"$(settings_file)" <<'JSON'
{
  "model": "opus",
  "enabledPlugins": { "superpowers@market": true },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit", "hooks": [ { "type": "command", "command": "/usr/local/bin/lint-edit" } ] }
    ],
    "Stop": [ { "hooks": [ { "type": "command", "command": "notify-send done" } ] } ]
  }
}
JSON
chmod 640 "$(settings_file)"
run_install
expect_status "adds the hook to existing settings" 0
expect_settings "keeps other keys and hooks, appends the hook" "{
  \"model\": \"opus\",
  \"enabledPlugins\": { \"superpowers@market\": true },
  \"hooks\": {
    \"PreToolUse\": [
      { \"matcher\": \"Edit\", \"hooks\": [ { \"type\": \"command\", \"command\": \"/usr/local/bin/lint-edit\" } ] },
      { \"matcher\": \"Bash\", \"hooks\": [ { \"type\": \"command\", \"command\": \"$(hook_path)\" } ] }
    ],
    \"Stop\": [ { \"hooks\": [ { \"type\": \"command\", \"command\": \"notify-send done\" } ] } ]
  }
}"
mode="$(file_mode "$(settings_file)")"
if [ "$mode" = 640 ]; then ok; else not_ok "keeps the file's mode" "expected 640, got $mode"; fi
expect_no_temp "leaves no temp file behind"

# --- a hook registered by hand (e.g. with a literal $HOME) counts; the file stays byte-identical ---
setup $'git\n' ''
mkdir -p "$SANDBOX/home/.claude"
# shellcheck disable=SC2016 # a hand-written entry with a literal $HOME, as a person would write it.
printf '%s\n' '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"$HOME/.claude/hooks/guard-commands.sh"}]}]},  "model":"opus"}' >"$(settings_file)"
cp "$(settings_file)" "$SANDBOX/before.json"
run_install
expect_status "hook already registered by hand" 0
expect_unchanged "hand-registered hook leaves settings.json byte-identical" "$SANDBOX/before.json"

# --- invalid JSON fails loudly and leaves the file untouched ---
setup $'git\n' ''
mkdir -p "$SANDBOX/home/.claude"
printf '{"model": "opus",\n' >"$(settings_file)"
cp "$(settings_file)" "$SANDBOX/before.json"
run_install
expect_status "invalid settings.json exits nonzero" 1
expect_err_contains "invalid settings.json names the file" "settings.json"
expect_unchanged "invalid settings.json stays untouched" "$SANDBOX/before.json"
expect_no_temp "invalid settings.json leaves no temp file behind"

# --- jq missing from PATH (after stow) ---
setup $'git\n' ''
HOME="$SANDBOX/home" PATH="$SANDBOX/bin:$NOJQ" "$BASH" "$SANDBOX/install" >"$SANDBOX/out" 2>"$SANDBOX/err"
status=$?
err="$(cat "$SANDBOX/err")"
expect_status "missing jq exits nonzero" 1
expect_err_contains "missing jq names jq" "jq not found"
if [ ! -e "$(settings_file)" ]; then ok; else not_ok "missing jq writes no settings.json"; fi

# --- local.md: the machine-local facts file that CLAUDE.md imports ---
# local_file — the sandbox's ~/.claude/local.md.
local_file() { printf '%s' "$SANDBOX/home/.claude/local.md"; }

# expect_local <description> <file holding the expected bytes>
expect_local() {
  if cmp -s "$2" "$(local_file)"; then ok; else not_ok "$1" "local.md holds: $(cat "$(local_file)" 2>&1)"; fi
}

# --- a missing local.md is created holding the stub ---
setup $'git\n' ''
run_install
expect_status "creates local.md" 0
cat >"$SANDBOX/stub-local.md" <<'EOF'
# This machine

Facts about this machine only: OS, shell, paths, installed tools, network.
`~/.claude/CLAUDE.md` imports this file; the dotfiles don't track it.
EOF
expect_local "new local.md holds the stub" "$SANDBOX/stub-local.md"

# --- re-running leaves local.md byte-identical ---
run_install
expect_status "re-run with local.md in place" 0
expect_local "re-run leaves local.md byte-identical" "$SANDBOX/stub-local.md"

# --- a local.md that is already there is left as is ---
setup $'git\n' ''
mkdir -p "$SANDBOX/home/.claude"
printf 'Omarchy on a ThinkPad, zsh\nno newline at the end' >"$(local_file)"
cp "$(local_file)" "$SANDBOX/before-local.md"
run_install
expect_status "local.md already there" 0
expect_local "existing local.md stays byte-identical" "$SANDBOX/before-local.md"

# --- a dangling link at local.md is already there too: nothing is written through it ---
setup $'git\n' ''
mkdir -p "$SANDBOX/home/.claude"
ln -s "$SANDBOX/elsewhere.md" "$(local_file)"
run_install
expect_status "dangling local.md link" 0
if [ -L "$(local_file)" ] && [ "$(readlink "$(local_file)")" = "$SANDBOX/elsewhere.md" ]; then
  ok
else
  not_ok "dangling local.md link stays the same link"
fi
if [ ! -e "$SANDBOX/elsewhere.md" ]; then ok; else not_ok "dangling local.md link's target is not created"; fi

# --- a local.md that can't be written stops the run ---
# install writes the stub with cat, so a cat that fails stands in for a failed write.
setup $'git\n' ''
printf '#!%s\nexit 1\n' "$BASH" >"$SANDBOX/bin/cat"
chmod +x "$SANDBOX/bin/cat"
run_install
expect_status "unwritable local.md exits nonzero" 1
expect_err_contains "unwritable local.md names the file" "could not write $(local_file)"

# --- the stowed CLAUDE.md imports the very path install writes the stub to ---
if grep -qxF '@~/.claude/local.md' "$REPO/claude/.claude/CLAUDE.md"; then
  ok
else
  not_ok "CLAUDE.md imports ~/.claude/local.md" "no line of claude/.claude/CLAUDE.md is exactly: @~/.claude/local.md"
fi

# --- plugins: each list line becomes one `claude plugin install`, in file order ---
setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\nformatter someone/their-plugins\n'
run_install
expect_status "two plugins" 0
expect_claude_calls "installs each plugin from its marketplace, in file order" \
  $'plugin install superpowers --marketplace anthropics/claude-plugins-official --scope user\nplugin install formatter --marketplace someone/their-plugins --scope user'

# --- plugins: comments, blank lines, trailing comments and whitespace are ignored ---
setup $'git\n' ''
write_plugin_list $'# header comment\n\n  superpowers   anthropics/claude-plugins-official  \n   \nformatter\tsomeone/their-plugins # trailing comment\n\t# indented comment\nlast-one some/where'
run_install
expect_status "parses the plugin list" 0
expect_claude_calls "plugin list skips comments/blanks, trims whitespace and trailing comments" \
  $'plugin install superpowers --marketplace anthropics/claude-plugins-official --scope user\nplugin install formatter --marketplace someone/their-plugins --scope user\nplugin install last-one --marketplace some/where --scope user'

# --- plugins: the real repo list feeds the real plugins ---
setup $'git\n' ''
cp "$REPO/packages/claude-plugins.txt" "$SANDBOX/packages/"
run_install
expect_status "repo plugin list" 0
expect_claude_calls "repo claude-plugins.txt installs superpowers and duckdb-skills" \
  $'plugin install superpowers --marketplace anthropics/claude-plugins-official --scope user\nplugin install duckdb-skills --marketplace anthropics/claude-plugins-official --scope user'

# --- plugins and MCP servers: comment-only lists are skipped, and then claude needn't be on PATH ---
setup $'git\n' ''
run_install
expect_status "comment-only plugin and MCP lists" 0
expect_claude_calls "comment-only plugin and MCP lists make no claude calls" ''

setup $'git\n' ''
rm "$SANDBOX/bin/claude"
run_install
expect_status "comment-only plugin and MCP lists run without claude on PATH" 0

# --- plugins: claude missing from PATH (after the steps before it) ---
setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\n'
rm "$SANDBOX/bin/claude"
run_install
expect_status "missing claude exits nonzero" 1
expect_err_contains "missing claude names claude" "claude not found"
expect_link "missing claude still stows first" .claude/CLAUDE.md
if [ -f "$(local_file)" ]; then ok; else not_ok "missing claude still creates local.md first"; fi

# --- plugins: a line that isn't `<plugin> <marketplace>` stops the run before any claude call ---
setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\nlonely-plugin\n'
run_install
expect_status "one-field plugin line exits nonzero" 1
expect_err_contains "one-field plugin line names the list" "claude-plugins.txt"
expect_err_contains "one-field plugin line shows the line" "lonely-plugin"
expect_claude_calls "one-field plugin line makes no claude calls, even after a good line" ''

setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\nformatter someone/their-plugins main\n'
run_install
expect_status "three-field plugin line exits nonzero" 1
expect_err_contains "three-field plugin line names the list" "claude-plugins.txt"
expect_err_contains "three-field plugin line shows the line" "formatter someone/their-plugins main"
expect_claude_calls "three-field plugin line makes no claude calls, even after a good line" ''

# --- plugins: a claude failure propagates, naming the plugin, its marketplace and the list ---
setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\nformatter someone/their-plugins\n'
STUB_CLAUDE_EXIT=1 run_install
expect_status "failing claude exits nonzero" 1
expect_err_contains "failure names the plugin" "superpowers"
expect_err_contains "failure names the marketplace" "anthropics/claude-plugins-official"
expect_err_contains "failure names the plugin list" "claude-plugins.txt"
expect_claude_calls "stops after the first failed plugin" \
  'plugin install superpowers --marketplace anthropics/claude-plugins-official --scope user'

# --- plugins: claude keeps install's stdin, stdout and stderr, so its prompt reaches a person ---
setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\nformatter someone/their-plugins\n'
cat >"$SANDBOX/bin/claude" <<EOF
#!$BASH
printf 'run this for %s? ' "\$3" >&2
IFS= read -r answer
printf '%s: %s\n' "\$3" "\$answer"
EOF
run_install <<<$'yes\nno'
expect_status "claude asks before it installs" 0
case "$out" in
  *$'superpowers: yes\nformatter: no'*) ok ;;
  *) not_ok "claude reads install's stdin and writes to its stdout" "stdout: $out" ;;
esac
expect_err_contains "claude's stderr comes through" "run this for superpowers? "

# --- MCP: a server no one registered is added, once `claude mcp get` shows the name is free ---
setup $'git\n' ''
write_mcp_list $'notes notes-server --stdio\n'
stub_command notes-server
run_install
expect_status "one MCP server" 0
expect_claude_calls "looks the server up, then adds it" \
  $'mcp get notes\nmcp add --scope user notes -- notes-server --stdio'

# --- MCP: a server that is already registered is left alone ---
setup $'git\n' ''
write_mcp_list $'notes notes-server --stdio\n'
stub_command notes-server
STUB_MCP_GET_EXIT=0 run_install
expect_status "MCP server already registered" 0
expect_claude_calls "a registered server gets no mcp add" 'mcp get notes'

# --- MCP: servers go in file order, and a command's arguments pass through in order ---
setup $'git\n' ''
write_mcp_list $'notes notes-server --stdio --root /tmp/x\nweb-pages browser-mcp\n'
stub_command notes-server
stub_command browser-mcp
run_install
expect_status "two MCP servers" 0
expect_claude_calls "registers each server in file order, with its arguments" \
  $'mcp get notes\nmcp add --scope user notes -- notes-server --stdio --root /tmp/x\nmcp get web-pages\nmcp add --scope user web-pages -- browser-mcp'

# --- MCP: a line is split on whitespace and nothing else: one word per field, globs as written ---
# This stub logs one word per line. `/*` would match something whatever the current dir is.
setup $'git\n' ''
write_mcp_list $'notes notes-server --only /* --root /tmp/x\n'
stub_command notes-server
cat >"$SANDBOX/bin/claude" <<EOF
#!$BASH
[ "\$2" = get ] && exit 1
printf '%s\n' "\$@" >>"$SANDBOX/claude-calls"
EOF
run_install
expect_status "MCP line with a glob" 0
expect_claude_calls "mcp add gets one word per field, unexpanded" \
  $'mcp\nadd\n--scope\nuser\nnotes\n--\nnotes-server\n--only\n/*\n--root\n/tmp/x'

# --- MCP: comments, blank lines and surrounding whitespace are ignored ---
setup $'git\n' ''
write_mcp_list $'# header comment\n\n  notes   notes-server\t--stdio  \n   \nweb-pages browser-mcp # trailing comment\n\t# indented comment\nlast last-server'
stub_command notes-server
stub_command browser-mcp
stub_command last-server
run_install
expect_status "parses the MCP list" 0
expect_claude_calls "MCP list skips comments/blanks, trims whitespace and trailing comments" \
  $'mcp get notes\nmcp add --scope user notes -- notes-server --stdio\nmcp get web-pages\nmcp add --scope user web-pages -- browser-mcp\nmcp get last\nmcp add --scope user last -- last-server'

# --- MCP: the real repo list registers the real servers ---
setup $'git\n' ''
cp "$REPO/packages/claude-mcp.txt" "$SANDBOX/packages/"
stub_command pulse
run_install
expect_status "repo MCP list" 0
expect_claude_calls "repo claude-mcp.txt registers pulse" \
  $'mcp get pulse\nmcp add --scope user pulse -- pulse mcp'

# --- MCP: claude missing from PATH ---
setup $'git\n' ''
write_mcp_list $'notes notes-server\n'
stub_command notes-server
rm "$SANDBOX/bin/claude"
run_install
expect_status "MCP list without claude exits nonzero" 1
expect_err_contains "MCP list without claude names claude" "claude not found"
expect_err_contains "MCP list without claude names the list" "claude-mcp.txt"

# --- MCP: a line with a name but no command stops the run before any claude call ---
setup $'git\n' ''
write_mcp_list $'notes notes-server\nlonely-server\n'
stub_command notes-server
run_install
expect_status "one-field MCP line exits nonzero" 1
expect_err_contains "one-field MCP line names the list" "claude-mcp.txt"
expect_err_contains "one-field MCP line shows the line" "lonely-server"
expect_claude_calls "one-field MCP line makes no claude calls, even after a good line" ''

# --- MCP: a server whose command isn't on PATH stops the run before claude hears of it ---
setup $'git\n' ''
write_mcp_list $'notes notes-server\nweb-pages browser-mcp --headless\n'
stub_command notes-server
run_install
expect_status "missing MCP command exits nonzero" 1
expect_err_contains "missing MCP command names the command" "browser-mcp"
expect_err_contains "missing MCP command names the server" "web-pages"
expect_err_contains "missing MCP command names the list" "claude-mcp.txt"
expect_claude_calls "missing MCP command gets no mcp get or mcp add" \
  $'mcp get notes\nmcp add --scope user notes -- notes-server'

# --- MCP: a failing `claude mcp add` propagates, naming the server and the list ---
setup $'git\n' ''
write_mcp_list $'journal notes-server\nweb-pages browser-mcp\n'
stub_command notes-server
stub_command browser-mcp
STUB_CLAUDE_EXIT=1 run_install
expect_status "failing mcp add exits nonzero" 1
expect_err_contains "mcp add failure names the server" "journal"
expect_err_contains "mcp add failure names the list" "claude-mcp.txt"
expect_claude_calls "stops after the first failed mcp add" \
  $'mcp get journal\nmcp add --scope user journal -- notes-server'

# --- MCP: `claude mcp get` is only a lookup, so its output is hidden; `mcp add` keeps its own ---
setup $'git\n' ''
write_mcp_list $'notes notes-server\n'
stub_command notes-server
cat >"$SANDBOX/bin/claude" <<EOF
#!$BASH
printf '%s says hello\n' "\$2"
printf '%s complains\n' "\$2" >&2
[ "\$2" = add ]
EOF
run_install
expect_status "claude mcp output" 0
case "$out" in
  *'add says hello'*) ok ;;
  *) not_ok "mcp add's stdout comes through" "stdout: $out" ;;
esac
expect_err_contains "mcp add's stderr comes through" 'add complains'
case "$out$err" in
  *'get says hello'* | *'get complains'*) not_ok "mcp get's output is hidden" "stdout: $out" "stderr: $err" ;;
  *) ok ;;
esac

# --- order: every plugin is installed before the first MCP server is looked up ---
setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\nformatter someone/their-plugins\n'
write_mcp_list $'notes notes-server\n'
stub_command notes-server
run_install
expect_status "plugins and MCP servers" 0
expect_claude_calls "every plugin call comes before the first mcp call" \
  $'plugin install superpowers --marketplace anthropics/claude-plugins-official --scope user\nplugin install formatter --marketplace someone/their-plugins --scope user\nmcp get notes\nmcp add --scope user notes -- notes-server'

# --- help ---
for flag in -h --help; do
  setup $'git\n' ''
  write_plugin_list $'superpowers anthropics/claude-plugins-official\n'
  run_install "$flag"
  expect_status "$flag exits 0" 0
  case "$out" in
    *Usage:*) ok ;;
    *) not_ok "$flag prints usage" "stdout: $out" ;;
  esac
  case "$out" in
    *stow*) ok ;;
    *) not_ok "$flag describes the stow step" "stdout: $out" ;;
  esac
  case "$out" in
    *settings.json*) ok ;;
    *) not_ok "$flag describes the hook registration" "stdout: $out" ;;
  esac
  case "$out" in
    *local.md*) ok ;;
    *) not_ok "$flag describes the local.md step" "stdout: $out" ;;
  esac
  case "$out" in
    *claude-plugins.txt*) ok ;;
    *) not_ok "$flag describes the plugin step" "stdout: $out" ;;
  esac
  case "$out" in
    *claude-mcp.txt*) ok ;;
    *) not_ok "$flag describes the MCP step" "stdout: $out" ;;
  esac
  expect_calls "$flag makes no omarchy calls" ''
  expect_claude_calls "$flag makes no claude calls" ''
done

# --- unknown argument ---
setup $'git\n' ''
write_plugin_list $'superpowers anthropics/claude-plugins-official\n'
run_install --bogus
expect_status "unknown argument exits 2" 2
expect_calls "unknown argument makes no omarchy calls" ''
expect_claude_calls "unknown argument makes no claude calls" ''

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" = 0 ]
