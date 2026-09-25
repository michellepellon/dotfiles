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
   edits go live at once. Repo-only files (`gotchas.md`, this plan) stay out of `$HOME` through stow's
   ignore list; confirm `.stow-local-ignore` once stow is installed. stow is in Arch `extra` (2.4.1). (2026-09-25)

## Open questions (settle in this order)

1. Repo layout for stow: one package at the repo root, or one package per app (`tmux/.config/tmux/...`)?
2. Package list: replaces the Brewfile. Check `omarchy pkg add` for how it fits.
3. Per app, keep, port or drop: tmux, Ghostty, vim, mutt (vim and mutt aren't installed).
4. Guard hook: drop the `timeout` rule; close the `git commit -n` and `core.hooksPath` holes
   test-first; decide how the hook gets registered in `~/.claude/settings.json`.

## Known facts

- Omarchy's Ghostty config already sends Shift+Enter as CSI-u, so our tmux `S-Enter` binding is obsolete.
- Clipboard on this box is `wl-copy`.

## State

Planning. Next step: open question 1 (stow layout).
