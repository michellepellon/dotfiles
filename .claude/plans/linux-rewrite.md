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

## Open questions (settle in this order)

1. Per app, keep, port or drop: tmux, Ghostty, vim, mutt (vim and mutt aren't installed).
2. Guard hook: drop the `timeout` rule; close the `git commit -n` and `core.hooksPath` holes
   test-first; decide how the hook gets registered in `~/.claude/settings.json`.
3. Which Brewfile packages carry over to the Arch/AUR lists.

## Known facts

- Omarchy's Ghostty config already sends Shift+Enter as CSI-u, so our tmux `S-Enter` binding is obsolete.
- Clipboard on this box is `wl-copy`.

## State

Planning. Next step: open question 1 (which apps to keep).
