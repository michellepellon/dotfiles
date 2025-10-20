# Vim Configuration

Deep dive into the vimrc configuration and customizations.

## Overview

The vimrc provides a clean, efficient development environment optimized for:
- Code editing with smart indentation and syntax highlighting
- Fast navigation with search and highlighting features
- Minimal distractions (no bells, clean status line)

## File Location

- **Source**: `~/dev/dotfiles/vimrc`
- **Symlink**: `~/.vimrc`

## General Settings

### History and Auto-reload
```vim
set history=500              " Remember 500 commands
set autoread                 " Auto-reload when file changes
au FocusGained,BufEnter * silent! checktime
```

### Leader Key
```vim
let mapleader = ","
```

All custom shortcuts use `,` as the leader key for easy access.

## User Interface

### Search Behavior
- **Case-smart searching**: Ignores case unless uppercase is used
- **Incremental search**: Shows matches as you type
- **Highlight results**: Visual feedback for all matches

```vim
set ignorecase
set smartcase
set hlsearch
set incsearch
```

### Visual Elements
- **Ruler**: Always shows cursor position
- **Wild menu**: Enhanced command-line completion
- **Match highlighting**: Shows matching brackets
- **Fold column**: 1-character left margin

### Disabled Annoyances
```vim
set noerrorbells
set novisualbell
```

No audio or visual bells on errors.

## Colors and Fonts

### Color Scheme
```vim
colorscheme desert
set background=dark
```

Desert colorscheme with dark background for reduced eye strain.

### Encoding
```vim
set encoding=utf8
set ffs=unix,dos,mac
```

UTF-8 encoding with Unix line endings as default.

## Indentation and Formatting

### Tab Settings
```vim
set expandtab                " Spaces instead of tabs
set smarttab                 " Smart tab behavior
set shiftwidth=4             " 4 spaces per indent level
set tabstop=4                " 4 spaces per tab
```

### Line Wrapping
```vim
set lbr                      " Line break on word boundaries
set tw=500                   " Wrap at 500 characters
set wrap                     " Enable line wrapping
```

### Auto-indenting
```vim
set ai                       " Auto indent
set si                       " Smart indent
```

## Status Line

### Format
```vim
set laststatus=2             " Always show status line
set statusline=\ %{HasPaste()}%F%m%r%h\ %w\ \ CWD:\ %r%{getcwd()}%h\ \ \ Line:\ %l\ \ Column:\ %c
```

Displays:
- Paste mode indicator (if active)
- Full file path
- Modified/read-only flags
- Current working directory
- Line and column numbers

## Key Mappings

### File Operations
| Shortcut | Action | Description |
|----------|--------|-------------|
| `,w` | `:w!<cr>` | Quick save |
| `:W` | `w !sudo tee %` | Save with sudo |

### Utilities
| Shortcut | Action | Description |
|----------|--------|-------------|
| `,m` | `:%s/<C-V><cr>//ge` | Remove Windows ^M characters |
| `,q` | `:e ~/buffer` | Open scratch buffer |
| `,x` | `:e ~/buffer.md` | Open markdown scratch buffer |
| `,pp` | `:setlocal paste!` | Toggle paste mode |

## Backup and Undo

### No Backup Files
```vim
set nobackup
set nowb
set noswapfile
```

Backup files disabled - rely on git for version control instead.

## Helper Functions

### HasPaste()
```vim
function! HasPaste()
    if &paste
        return 'PASTE MODE  '
    endif
    return ''
endfunction
```

Shows "PASTE MODE" in status line when paste mode is active.

## Performance Settings

### Lazy Redraw
```vim
set lazyredraw               " Don't redraw during macros
set regexpengine=0           " Auto-select regex engine
```

Optimizes performance when running macros or complex operations.

## Customization

To modify vim settings:

1. Edit source file:
   ```bash
   vim ~/dev/dotfiles/vimrc
   ```

2. Reload configuration:
   ```vim
   :source ~/.vimrc
   ```

Changes persist across sessions through the symlink.
