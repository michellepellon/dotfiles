# Gotchas

## Being rewritten Linux-only; macOS support is dropped
The configs still assume a Mac (`macos-icon` in Ghostty), but the repo is being rewritten for Linux (Omarchy/Arch) only. Port or delete Mac-only pieces; don't preserve them. Omarchy owns some target configs (`~/.config/tmux`, `~/.config/ghostty`), so test in isolation (`tmux -L scratch -f ...`), never by overwriting `$HOME`.

## No Co-Authored-By trailers
Commit messages in this repo end at the body. Leave out `Co-Authored-By:` lines, even if your tool adds them by default.

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
