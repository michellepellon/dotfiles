# Linux rewrite plan

Rewrite these dotfiles for Omarchy (Arch + Hyprland), one decision at a time.
Omarchy 4.0.4 on the target box.

## Decisions

1. **Linux only.** Drop macOS support: Brewfile, `pbcopy`, `macos-icon`, Mac keybinds. (2026-09-25)
2. **Layer on top of Omarchy, app by app, as we go.** Never edit `/usr/share/omarchy/`. (2026-09-25)
   How each app layers, from reading the configs on the box:
   - **Hyprland:** `hyprland.lua` loads Omarchy defaults, then `~/.config/hypr/*.lua`. Edit those user files.
   - **tmux:** `~/.config/tmux/tmux.conf` is a plain copy of Omarchy's default. Ours should
     `source-file /usr/share/omarchy/config/tmux/tmux.conf` first, then set our options; later lines win.
   - **Ghostty:** `~/.config/ghostty/config` is also a plain copy. Included files load *after* the
     including file (`ghostty +show-config --default --docs`), so ours lists
     `config-file = /usr/share/omarchy/config/ghostty/config` and then `config-file = <our overrides>`.
     Untested: whether Omarchy's nested theme include loads before our overrides. Test before overriding colors.
3. **GNU stow manages the dotfiles.** It symlinks from this checkout into `$HOME`, so there's one copy and
   edits go live at once. stow is in Arch `extra` (2.4.1). (2026-09-25)
4. **One stow package per app.** e.g. `tmux/.config/tmux/tmux.conf`, `claude/.claude/CLAUDE.md`,
   `claude/.claude/hooks/guard-commands.sh`; install with `stow -t ~ tmux claude ...`. Repo-only files
   (`gotchas.md`, `.claude/plans/`) sit outside every package, so no ignore list is needed. (2026-09-25)
5. **Packages live in text lists plus a script.** `packages/arch.txt` and `packages/aur.txt`, one name per
   line, fed to `omarchy pkg add` / `omarchy pkg aur add` (both skip what's installed) by a small script
   with help text and tests. Replaces the Brewfile. (2026-09-25)
6. **Port tmux, Ghostty and mutt; drop vim.** Neovim 0.12 ships with Omarchy, so `.vimrc` goes.
   - tmux: layer prefix, splits and vi keys over Omarchy's config; `pbcopy` becomes `wl-copy`; drop `S-Enter`.
   - Ghostty: layer only settings Omarchy doesn't already cover (theme, font, Shift+Enter are covered;
     opacity/blur belong to Hyprland).
   - mutt: not installed; add `mutt` (Arch `extra`, 2.4.2) to the package list. Password stays in
     `~/.mutt/credentials`, outside the repo. (2026-09-25)
7. **Guard hook: keep rules 1–2, drop `timeout`, and let the install script register it.** Close the
   `git commit -n` and `git -c core.hooksPath=...` holes test-first. The install script merges the hook
   entry into `~/.claude/settings.json` with jq only if it's missing; the file itself stays untracked
   because Claude Code rewrites it. Add `jq` to the package list. (2026-09-25)
8. **Package list contents.** (2026-09-25)
   - `packages/arch.txt`: `aws-cli-v2`, `duckdb`, `uv`, `bitwarden`, `tmux`, `ghostty`, `git`, `ast-grep`,
     `stow`, `jq`, `mutt`. Omarchy installs some of these today; we list them because our configs depend on them.
   - `packages/aur.txt`: empty for now.
   - Dropped from the Brewfile: `htop` (Omarchy ships `btop`), `spaceship` (zsh prompt; Omarchy uses `starship`),
     `yadm` (stow replaces it), `docker-desktop` (`docker` is installed), `google-chrome`, `zoom`,
     `granola`, `pareto-security`.
   - `gh` stays in mise, where it's installed; don't add `github-cli`.

## Known facts

- Omarchy's Ghostty config already sends Shift+Enter as CSI-u, so our tmux `S-Enter` binding is obsolete.
- Clipboard on this box is `wl-copy`.
- On Arch the ast-grep command is `ast-grep`, not `sg`; `CLAUDE.md` still says `sg`. Fix it.
- `~/.claude/CLAUDE.md` exists as a real file, so the first `stow claude` conflicts; use `--adopt` or move it first.

## State

Planning done: all decisions made. Next step: break the work into phases for subagents.
