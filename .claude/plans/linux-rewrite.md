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
- On Arch the ast-grep command is `ast-grep`, not `sg`; `claude/.claude/CLAUDE.md` says `ast-grep`.
- `~/.claude/CLAUDE.md` exists as a real file, so the first `stow claude` conflicts. Don't use `--adopt`: it moves the home file into the repo, replacing the repo copy. Move the home file aside by hand, with Michelle's go-ahead.

## Phases

One branch and one PR per phase, merged in order. Each phase is handed to an implementer subagent, then
reviewed, then checked by the orchestrator. Bash scripts and tests follow the style of
`guard-commands.sh` / `guard-commands.test.sh`. Nothing touches the real `$HOME` or installs packages
without Michelle's go-ahead: tests use scratch dirs, and each phase's live run is a separate, approved step.

1. **Package lists and install script.** Add `packages/arch.txt` and `packages/aur.txt` (decision 8) and
   an `install` script at the repo root that feeds them to `omarchy pkg add` / `omarchy pkg aur add`,
   skipping blank lines and `#` comments. `--help`, clear errors, tests. Delete the Brewfile.
   Live run (approval needed): `./install` installs stow, mutt, uv and the rest. ~120 LOC.
2. **stow layout and the claude package.** Move `.claude/CLAUDE.md` and `.claude/hooks/` into
   `claude/.claude/`; `.claude/plans/` stays at the repo root. `install` gains a stow step
   (`stow -t ~ <packages>`) that stops with a clear message on conflicts like the real
   `~/.claude/CLAUDE.md`, never overwriting it. Fix `sg` → `ast-grep` in `CLAUDE.md`. Delete `.vimrc`.
   Tests stow into a scratch target. Live run (approval needed): first real stow. ~80 LOC.
3. **Guard hook.** Drop the `timeout` rule and its tests. Close the `git commit -n` and
   `git -c core.hooksPath=...` holes, failing tests first. `install` merges the hook entry into
   `~/.claude/settings.json` with jq only if it's missing; tests run against a temp settings file. ~70 LOC.
4. **tmux package.** `tmux/.config/tmux/tmux.conf` sources Omarchy's default, then layers the prefix,
   splits and vi keys from the old config; `wl-copy` replaces `pbcopy`; no `S-Enter`. Check it with
   `tmux -L <scratch>`. Add `tmux` to the stow list. ~60 LOC.
5. **Ghostty package.** Layer only settings Omarchy doesn't cover, via two `config-file` includes
   (decision 2). First test whether Omarchy's nested theme include loads before our overrides.
   Add `ghostty` to the stow list. ~20 LOC.
6. **mutt package.** Move `.muttrc` into `mutt/`. Check whether mutt creates `~/.mutt/cache` itself; if not,
   `install` creates it. Michelle writes `~/.mutt/credentials` by hand; it never enters the repo.
   Add `mutt` to the stow list. ~20 LOC.
7. **Wrap-up.** Remove leftover Mac files, rewrite the `gotchas.md` entry now that the rewrite has landed,
   update memory, and mark this plan done. ~20 LOC.

Phases 3–6 each add to the stow list in `install`, so they run one after another, not in parallel.

## State

Phase 1 done: live run installed aws-cli-v2, duckdb, uv, bitwarden, stow and mutt (2026-09-25);
a re-run is a no-op.

Phase 2 implemented on `feat/stow-claude`: `claude/.claude/` holds `CLAUDE.md` and the guard hook,
`.vimrc` is gone, and `install` ends with `stow --no-folding -d <repo> -t $HOME claude` (the
`stow_packages` list near its top). Live stow pending Michelle's approval: the real
`~/.claude/CLAUDE.md` must be moved aside first, or `./install` stops at the conflict.
Next step: phase 2 review, then its live run.

Phase 3 implemented on `feat/guard-hook`: the guard hook drops the `timeout` rule and blocks
`git commit -n` (alone or bundled) and `core.hooksPath` overrides (`git -c`, `--config-env`,
`git config` setting it); `install` ends by registering the hook in `$HOME/.claude/settings.json`
with jq (absolute path, appended only if no PreToolUse command already ends in
`/.claude/hooks/guard-commands.sh`). Live registration into the real `~/.claude/settings.json`
pending Michelle's approval. Next step: phase 3 review, then its live run.
