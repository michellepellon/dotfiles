# Gotchas

## Being rewritten Linux-only; macOS support is dropped
The configs still assume a Mac (Brewfile casks, `pbcopy` in tmux, `macos-icon` in Ghostty, yadm to install), but the repo is being rewritten for Linux (Omarchy/Arch) only. Port or delete Mac-only pieces; don't preserve them. The guard hook's `timeout` block is Mac-era and wrong on Linux. Omarchy owns some target configs (`~/.config/tmux`, `~/.config/ghostty`), so test in isolation (`tmux -L scratch -f ...`), never by overwriting `$HOME`.

## No Co-Authored-By trailers
Commit messages in this repo end at the body. Leave out `Co-Authored-By:` lines, even if your tool adds them by default.
