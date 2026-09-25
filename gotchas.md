# Gotchas

## These dotfiles target macOS
The configs assume a Mac: Brewfile casks, `pbcopy` in tmux, `macos-icon` in Ghostty, yadm to install. A checkout on a Linux box (e.g. Omarchy) doesn't deploy them. The guard hook's `timeout` block assumes the Mac, where `timeout` isn't installed; Linux has it. Test configs in isolation (`tmux -L scratch -f ...`), never by overwriting `$HOME`.

## No Co-Authored-By trailers
Commit messages in this repo end at the body. Leave out `Co-Authored-By:` lines, even if your tool adds them by default.
