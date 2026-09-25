#!/usr/bin/env bash
# ABOUTME: Tests for install — runs it against scratch package lists with a stub omarchy
# ABOUTME: that records its arguments. Run: ./install.test.sh (nonzero if any fail).

set -u
REPO="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
pass=0
fail=0

# The real omarchy sits in /usr/bin and /usr/share/omarchy/bin, so tests never put system
# dirs on PATH: it holds only the stub and $TOOLS (symlinks to what install needs), and
# bash runs by absolute path. No test can reach the real omarchy or install anything.
TOOLS="$SCRATCH/tools"
mkdir -p "$TOOLS"
for tool in dirname cat; do ln -s "$(command -v "$tool")" "$TOOLS/$tool"; done

ok() { pass=$((pass + 1)); }
not_ok() {
  fail=$((fail + 1))
  printf 'FAIL: %s\n' "$1"
  shift
  [ $# -gt 0 ] && printf '      %s\n' "$@"
}

# setup <arch-list-contents> <aur-list-contents> — fresh sandbox with a copy of install,
# the given lists, and a stub omarchy that appends "$*" to $SANDBOX/calls and exits $STUB_EXIT.
setup() {
  SANDBOX="$(mktemp -d "$SCRATCH/case.XXXXXX")"
  cp "$REPO/install" "$SANDBOX/install"
  mkdir -p "$SANDBOX/packages" "$SANDBOX/bin"
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

# run_install [args...] — runs the sandbox copy with the stub first on PATH; sets
# $status, $out and $err.
run_install() {
  PATH="$SANDBOX/bin:$TOOLS" "$BASH" "$SANDBOX/install" "$@" \
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
  'pkg add aws-cli-v2 duckdb uv bitwarden tmux ghostty git ast-grep stow jq mutt'

# --- omarchy missing from PATH ---
setup $'git\n' ''
PATH="$TOOLS" "$BASH" "$SANDBOX/install" >"$SANDBOX/out" 2>"$SANDBOX/err"
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

# --- help ---
for flag in -h --help; do
  setup $'git\n' ''
  run_install "$flag"
  expect_status "$flag exits 0" 0
  case "$out" in
    *Usage:*) ok ;;
    *) not_ok "$flag prints usage" "stdout: $out" ;;
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
