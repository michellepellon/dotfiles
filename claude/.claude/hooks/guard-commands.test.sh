#!/usr/bin/env bash
# ABOUTME: Tests for guard-commands.sh — feeds sample PreToolUse payloads and asserts
# ABOUTME: block (exit 2) vs allow (exit 0). Run: ./guard-commands.test.sh (nonzero if any fail).

set -u
HOOK="$(cd "$(dirname "$0")" && pwd)/guard-commands.sh"
pass=0
fail=0

# check <description> <expected_exit> <command> [tool_name=Bash]
check() {
  local desc="$1" want="$2" cmd="$3" tool="${4:-Bash}" payload got
  payload=$(jq -nc --arg t "$tool" --arg c "$cmd" '{tool_name:$t, tool_input:{command:$c}}')
  printf '%s' "$payload" | "$HOOK" >/dev/null 2>&1
  got=$?
  if [ "$got" = "$want" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf 'FAIL: %s\n      cmd: %s\n      expected exit %s, got %s\n' "$desc" "$cmd" "$want" "$got"
  fi
}

# --- should BLOCK (exit 2) ---
check "no-verify on commit"       2 'git commit --no-verify -m "x"'
check "no-verify trailing"        2 'git commit -m "x" --no-verify'
check "no-verify on push"         2 'git push --no-verify'
check "no-pre-commit-hook"        2 'git commit --no-pre-commit-hook -m "x"'
check "abbreviated --no-verif"    2 'git commit --no-verif -m "x"'
check "abbreviated --no-veri"     2 'git commit --no-veri -m "x"'
check "abbreviated on push"       2 'git push --no-verif'
check "pip install"               2 'pip install requests'
check "pip3 install"              2 'pip3 install requests'
check "python -m pip install"     2 'python -m pip install requests'
check "sudo pip install"          2 'sudo pip install requests'
check "poetry add"                2 'poetry add requests'
check "easy_install"              2 'easy_install requests'
check "pip after &&"              2 'cd /tmp && pip install x'
check "commit -n"                 2 'git commit -n -m "x"'
check "commit -nm combined"       2 'git commit -nm "x"'
check "commit -an combined"       2 'git commit -an -m "x"'
check "commit -n after &&"        2 'git add . && git commit -n -m "x"'
check "-c core.hooksPath"         2 'git -c core.hooksPath=/dev/null commit -m "x"'
check "-c core.hookspath lower"   2 'git -c core.hookspath=/dev/null commit -m "x"'
check "config core.hooksPath"     2 'git config core.hooksPath /dev/null'
check "config --global hooksPath" 2 'git config --global core.hooksPath /tmp/none'
check "config --local HOOKSPATH"  2 'git config --local CORE.HOOKSPATH .nohooks'
check "config set hooksPath"      2 'git config set core.hooksPath /dev/null'
check "--config-env hooksPath"    2 'git --config-env=core.hooksPath=NOHOOKS commit -m "x"'

# --- should ALLOW (exit 0) ---
check "uv pip install"            0 'uv pip install requests'
check "uv add"                    0 'uv add requests'
check "pip inside commit msg"     0 'git commit -m "docs: how to pip install foo"'
check "plain commit"              0 'git commit -m "fix bug"'
check "curl --connect-timeout"    0 'curl --connect-timeout 5 https://example.com'
check "echo mentions pip"         0 'echo "run pip install later"'
check "npm install"               0 'npm install'
check "plain ls"                  0 'ls -la'
check "commit -am"                0 'git commit -am "x"'
check "-n inside commit msg"      0 'git commit -m "fix -n handling"'
check "log -n"                    0 'git log -n 5'
check "clean -n dry run"          0 'git clean -n'
check "push -n dry run"           0 'git push -n'
check "merge -n"                  0 'git merge -n feature'
check "config --get hooksPath"    0 'git config --get core.hooksPath'
check "config read hooksPath"     0 'git config core.hooksPath'
check "config get hooksPath"      0 'git config get core.hooksPath'
check "read hooksPath 2>/dev/null" 0 'git config --get core.hooksPath 2>/dev/null'
check "set hooksPath >/dev/null"  2 'git config core.hooksPath /x >/dev/null'
check "config --unset hooksPath"  0 'git config --unset core.hooksPath'
check "commit -uno"               0 'git commit -uno -m "x"'
check "timeout runs directly"     0 'timeout 5 ./run.sh'

# --- non-Bash tools are ignored even with a matching command field ---
check "non-Bash tool ignored"     0 'pip install requests' 'Edit'

# --- fail-open: malformed stdin must not block ---
if printf 'not valid json' | "$HOOK" >/dev/null 2>&1; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL: malformed JSON should exit 0 (fail-open)"; fi

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" = 0 ]
