#!/usr/bin/env bash
# ABOUTME: Tests for install — runs it against scratch package lists with a stub omarchy
# ABOUTME: and real stow into a scratch HOME. Run: ./install.test.sh (nonzero if any fail).

set -u
REPO="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
pass=0
fail=0

# The real omarchy sits in /usr/bin and /usr/share/omarchy/bin, so tests never put system
# dirs on PATH: it holds only the stub and $TOOLS (symlinks to what install needs), and
# bash runs by absolute path. No test can reach the real omarchy or install anything.
# stow is real; every run sets HOME to a scratch dir, so it only links into that.
# jq is real too and only ever edits $SANDBOX/home/.claude/settings.json.
# NOSTOW is TOOLS without stow; NOJQ is TOOLS without jq.
TOOLS="$SCRATCH/tools"
NOSTOW="$SCRATCH/nostow"
NOJQ="$SCRATCH/nojq"
mkdir -p "$TOOLS" "$NOSTOW" "$NOJQ"
for tool in dirname cat mv rm chmod; do
  ln -s "$(command -v "$tool")" "$TOOLS/$tool"
  ln -s "$(command -v "$tool")" "$NOSTOW/$tool"
  ln -s "$(command -v "$tool")" "$NOJQ/$tool"
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
# the given lists, a copy of the claude stow package, a repo-only .claude/plans file, an
# empty $SANDBOX/home to stow into, and a stub omarchy that appends "$*" to $SANDBOX/calls
# and exits $STUB_EXIT.
setup() {
  SANDBOX="$(mktemp -d "$SCRATCH/case.XXXXXX")"
  cp "$REPO/install" "$SANDBOX/install"
  cp -R "$REPO/claude" "$SANDBOX/claude"
  mkdir -p "$SANDBOX/packages" "$SANDBOX/bin" "$SANDBOX/home" "$SANDBOX/.claude/plans"
  printf 'plan\n' >"$SANDBOX/.claude/plans/plan.md"
  printf '%s' "$1" >"$SANDBOX/packages/arch.txt"
  printf '%s' "$2" >"$SANDBOX/packages/aur.txt"
  cat >"$SANDBOX/bin/omarchy" <<EOF
#!$BASH
printf '%s\n' "\$*" >>"$SANDBOX/calls"
exit "\${STUB_EXIT:-0}"
EOF
  chmod +x "$SANDBOX/bin/omarchy"
  : >"$SANDBOX/calls"
}

# run_install [args...] — runs the sandbox copy with the stub first on PATH and HOME set
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
setup $'git\nmutt' ''
run_install
expect_calls "reads a final line with no newline" 'pkg add git mutt'

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
  'pkg add aws-cli-v2 duckdb uv bitwarden tmux ghostty git ast-grep stow jq mutt shellcheck'

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
  not_ok "~/.claude and ~/.claude/hooks are real dirs, not links into the repo"
fi
if [ ! -e "$SANDBOX/home/.claude/plans" ]; then ok; else not_ok ".claude/plans is never stowed"; fi

# --- stow: re-running on a stowed HOME is a no-op ---
run_install
expect_status "re-run on a stowed home" 0
expect_link "re-run keeps the CLAUDE.md link" .claude/CLAUDE.md

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
mode="$(stat -c %a "$(settings_file)")"
if [ "$mode" = 640 ]; then ok; else not_ok "keeps the file's mode" "expected 640, got $mode"; fi
expect_no_temp "leaves no temp file behind"

# --- a hook registered by hand (e.g. with a literal $HOME) counts; the file stays byte-identical ---
setup $'git\n' ''
mkdir -p "$SANDBOX/home/.claude"
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

# --- help ---
for flag in -h --help; do
  setup $'git\n' ''
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
  expect_calls "$flag makes no omarchy calls" ''
done

# --- unknown argument ---
setup $'git\n' ''
run_install --bogus
expect_status "unknown argument exits 2" 2
expect_calls "unknown argument makes no omarchy calls" ''

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" = 0 ]
