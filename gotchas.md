# Gotchas

## Omarchy first; macOS gets packages and Claude config only
These dotfiles target Omarchy (Arch + Hyprland). On a Mac, `./install` installs `packages/brew.txt` and `packages/cask.txt` with Homebrew, stows `claude` and registers the guard hook; no app configs are kept for macOS. A package added for one system needs its twin in the other system's list (names differ: `aws-cli-v2` is `awscli` in Homebrew).

## install must run on bash 3.2 and BSD tools
macOS ships bash 3.2 and BSD userland, and `install` runs under them: no `mapfile`, no `chmod --reference`, no `stat -c`. `install.test.sh` stubs `uname` (`STUB_OS`), so both paths are tested on either system, but only a run on the real system proves the tools behave. Run the suite on both before merging a change to `install`.

## Omarchy owns most app configs
Omarchy owns most app configs (`~/.config/tmux`, `~/.config/ghostty`, `~/.config/hypr`), and tmux and Ghostty run on its defaults unchanged. Before adding a config here, check what Omarchy already sets, and test in isolation (`tmux -L scratch -f ...`), never by overwriting `$HOME`.

## No Co-Authored-By trailers
Commit messages in this repo end at the body. Leave out `Co-Authored-By:` lines, even if your tool adds them by default. For Claude Code the repo's `.claude/settings.json` helps: `attribution.commit` is `""`, so a session started in this directory is never told to add the trailer. A session started somewhere else and pointed here still is, and so are other tools, so the rule stands.

## omarchy is in /usr/bin too
Omarchy installs its commands in both `/usr/share/omarchy/bin` and `/usr/bin`, so a stub `omarchy` on PATH doesn't shield tests if `/usr/bin` follows it. `install.test.sh` gives the script a PATH with only the stub and symlinks to the tools it needs, and runs bash by absolute path (`$BASH`).

## Package conflicts make ./install fail
`omarchy pkg add` runs pacman with `--noconfirm`, which answers "no" to "remove the conflicting package?", so one conflict aborts the whole transaction and nothing installs. Before adding a package that replaces another (e.g. `aws-cli-v2` over `aws-cli`), remove the old one by hand. `./install` needs a real terminal for its sudo prompt; Claude Code's `!` prefix has none.

## stow runs with --no-folding
Without it, stow links a whole missing directory into the repo (`~/.claude/hooks` on this box, `~/.claude` itself on a fresh one), so files that apps write there land in the checkout. `install` passes `--no-folding`. On any conflict stow 2.4.1 aborts the whole run and changes nothing. `install.test.sh` runs the real stow, so every install call in it must set `HOME` to a scratch dir.

## Live config follows the checked-out branch
Once stowed, `~/.claude/CLAUDE.md` and the guard hook are symlinks into this checkout. Checking out a branch or commit without `claude/` (anything before phase 2) breaks the links, and Claude Code silently starts with no global instructions. Keep `~/Work/dotfiles` on `main` or a branch cut from it; after switching, check `ls -L ~/.claude/CLAUDE.md`.

## `!` means different things in Claude Code and zsh
In Claude Code's prompt, a leading `!` runs the command in the session. In a real zsh shell, `!` negates the exit status, so `! mv a b && ./install` treats mv's success as failure and skips `./install`. Say where each command should run. Anything needing sudo goes in a real terminal, because `!` has no TTY.

## The guard hook blocks text that mentions bypass flags
Rule 1 blocks any Bash command containing `git` plus `--no-veri`/`--no-hooks`/`--no-pre-commit-hook`, even inside quotes. When a commit message, PR body or edit script mentions those flags, write the text to a file (Write tool) and pass the file: `git commit -F`, `gh pr create --body-file`, `python3 script.py`. No flag reaches git, so this isn't a bypass.

## Claude Code plugins come from packages/claude-plugins.txt
One `<plugin> <marketplace>` pair per line. `./install` runs `claude plugin install <plugin> --marketplace <marketplace> --scope user` for each, every time: the command exits 0 when the plugin is already installed and adds a marketplace it doesn't know yet, so `install` keeps no state and reads no JSON. It never passes `-y`. A plugin whose marketplace declares a command to run then stops and shows that command, which is the point: a person must read it. The official marketplace pins each plugin to a commit, so it can trail the author's own marketplace. To the CLI the same plugin from another marketplace is a different plugin: if one was installed by hand, run `claude plugin uninstall` on it first, or both load. In every list a `#` starts a comment only at the start of a line or after whitespace, so `owner/repo#ref` pins a marketplace.

## Try claude CLI changes in a scratch config first
`CLAUDE_CONFIG_DIR=<scratch dir> claude plugin ...` (or `claude mcp ...`) gives the CLI its own `settings.json`, `.claude.json` and `plugins/`, so nothing touches `~/.claude`. A fresh config knows no marketplace, not even the official one. `./install` meets that state on a machine where Claude Code has never run, which is why it passes `--marketplace`.

## ~/.claude/local.md is per machine
`CLAUDE.md` ends with `@~/.claude/local.md`. Facts about one machine (OS, shell, installed tools) go in that file, never in `CLAUDE.md`, which every machine shares. `./install` creates a stub when the file is missing and never edits an existing one. The dotfiles don't track it.

## Skills in the claude package; ~/.claude/skills stays a real directory
`claude/.claude/skills/uv/SKILL.md` is a copy from harperreed/dotfiles, so it carries no ABOUTME lines; update it by copying again. Claude Code keeps its own files under `~/.claude/skills` (`synced/`), which is one more reason stow runs with `--no-folding`: only `SKILL.md` is a link.

## MCP servers come from packages/claude-mcp.txt
One `<name> <command> [args...]` line per server. `./install` registers each with `claude mcp add --scope user <name> -- <command> [args...]`, but only after `claude mcp get <name>`, run from an empty directory, fails to find the name: a second `add` of the same name fails. The empty directory matters, because `mcp get` also finds a server registered for just the directory it runs in. It starts each server it finds, to check it. User-scope servers live in `~/.claude.json`. `mcpServers` is not a `settings.json` key, whatever a tool's README says. The command must be on PATH first, or `./install` stops. A registered server is never updated: after changing its line, run `claude mcp remove <name> -s user`, then `./install`.

## pulse is the journal, and Omarchy has no package for it
`CLAUDE.md` tells the agent to journal; pulse (`2389-research/pulse`) is the tool. It keeps Markdown under `~/.private-journal/`, and its search is a plain substring match. macOS gets it from `brew.txt`, out of a third-party tap. On Omarchy put the Linux release binary on PATH by hand. Never add the AUR's `pulse-bin` to `aur.txt`: that is a different program, a network monitor.
