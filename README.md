# Dotfiles

Personal development environment configuration including Vim, Claude Code, and 
conversation memory system.

## Features

- **Vim Configuration** - Desert colorscheme, 4-space indentation, custom status line
- **Claude Code Configuration** - Coding standards, TDD workflow, collaboration guidelines
- **Skills System** - Modular skills for test-driven development and conversation memory
- **Semantic Search** - Search past Claude Code conversations using natural language or exact text matching

## Quick Start

### Prerequisites

- **Node.js** (v16+) - [Install from nodejs.org](https://nodejs.org) or use [nvm](https://github.com/nvm-sh/nvm)
- **npm** - Comes with Node.js
- **git** - To clone this repository

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/michellepellon/dotfiles.git ~/dev/dotfiles
   cd ~/dev/dotfiles
   ```

2. Run the installation script:
   ```bash
   ./install.sh
   ```

3. Restart your terminal or reload your shell configuration:
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

That's it! The installation script will:
- ✅ Check prerequisites (Node.js, npm)
- ✅ Backup any existing dotfiles
- ✅ Create symlinks to your home directory
- ✅ Install conversation search dependencies
- ✅ Set up automatic conversation archiving

## What Gets Installed

### Symlinks Created

| Source | Target | Description |
|--------|--------|-------------|
| `vimrc` | `~/.vimrc` | Vim configuration |
| `.claude/CLAUDE.md` | `~/.claude/CLAUDE.md` | Global Claude Code instructions |
| `.claude/commands/` | `~/.claude/commands/` | Slash commands (brainstorm, plan, session-summary, setup) |
| `.claude/skills/` | `~/.claude/skills/` | Skills (TDD, conversation memory) |

### Additional Setup

- **Conversation Search Tool** - Node.js dependencies installed in `~/.claude/skills/collaboration/remembering-conversations/tool/`
- **sessionEnd Hook** - Installed at `~/.claude/hooks/sessionEnd` for automatic conversation archiving

## Usage

### Vim

Just open vim - configuration is automatically loaded:
```bash
vim myfile.py
```

### Claude Code

Claude Code automatically loads `~/.claude/CLAUDE.md` when starting a session.

#### Available Commands

- `/brainstorm` - Interactive spec development through questionnaires
- `/plan` - Create multi-level project plans from specs
- `/session-summary` - Generate timestamped session reports
- `/setup` - Validate Claude configuration exists

#### Claude Skills

Three comprehensive skills that activate automatically when relevant:

##### 1. Test-Driven Development (`testing/test-driven-development`)

**When it activates**: All coding tasks (features, bug fixes, refactoring)

**What it does**:
- Enforces strict TDD workflow: write test → run → implement → refactor
- Requires unit, integration, and end-to-end tests
- No mocks policy - uses real data and APIs
- Ensures pristine test output

**Files**: 5 (SKILL.md, examples, reference, templates)

**Location**: `.claude/skills/testing/test-driven-development/`

##### 2. Remembering Conversations (`collaboration/remembering-conversations`)

**When it activates**: When you mention "we discussed this before" or similar issues arise

**What it does**:
- Automatically archives all conversations after each session
- Generates AI-powered summaries (50-120 words)
- Enables semantic search using vector embeddings
- Supports exact text search for git SHAs, error messages
- Uses subagent pattern for 50-100x context savings

**Features**:
- Vector similarity search for concepts
- Text search for exact matches
- Time-range filtering
- SQLite database with sqlite-vec
- Background indexing via sessionEnd hook

**Files**: 29 (TypeScript implementation, tests, docs)

**Location**: `.claude/skills/collaboration/remembering-conversations/`

**Search examples**:
```bash
# Semantic search
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations "React Router auth errors"

# Find git SHA
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --text "a1b2c3d4"

# Time range
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --after 2025-09-01 "refactoring"
```

##### 3. Quick Descriptive Stats (`analysis/quick-descriptive-stats`)

**When it activates**: When a CSV file is uploaded or tabular data analysis is requested

**What it does**:
- Proactively analyzes CSV files without asking questions
- Generates comprehensive statistics (mean, median, std, correlations)
- Creates adaptive visualizations based on data types
- Reports data quality issues (missing values)
- Produces correlation heatmaps, time-series plots, distributions

**Features**:
- Automatic data type detection
- Correlation analysis for numeric columns
- Time-series plotting for date columns
- Categorical breakdowns
- Distribution histograms
- All analysis runs immediately - no user prompting

**Code quality**:
- 476 lines of implementation (11 modular functions)
- 200+ lines of tests (16 tests across 4 test files)
- Full type annotations
- Comprehensive error handling

**Files**: 15 (implementation, tests, fixtures, docs)

**Location**: `.claude/skills/analysis/quick-descriptive-stats/`

**Dependencies**: pandas, matplotlib, seaborn (install with `pip3 install -r requirements.txt`)

### Conversation Memory

Conversations are automatically archived and indexed after each session.

#### Search Past Conversations

Semantic search (finds similar concepts):
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations "React Router authentication errors"
```

Exact text match (for git SHAs, error messages):
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --text "a1b2c3d4"
```

Time filtering:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --after 2025-09-01 "refactoring"
```

See full options:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --help
```

#### Manual Indexing

Conversations are indexed automatically via the sessionEnd hook. To manually index:

```bash
# Index all unprocessed conversations
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --cleanup

# Check index health
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --verify

# Fix any issues
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --repair
```

## Repository Structure

```
dotfiles/
├── install.sh                  # Installation script
├── README.md                   # This file
├── vimrc                       # Vim configuration
└── .claude/
    ├── CLAUDE.md              # Global Claude Code instructions
    ├── commands/              # Slash commands
    │   ├── brainstorm.md
    │   ├── plan.md
    │   ├── session-summary.md
    │   └── setup.md
    └── skills/                # Claude Code skills
        ├── testing/
        │   └── test-driven-development/
        │       ├── SKILL.md
        │       ├── examples.md
        │       ├── reference.md
        │       └── templates/
        └── collaboration/
            └── remembering-conversations/
                ├── SKILL.md
                ├── INDEXING.md
                ├── DEPLOYMENT.md
                └── tool/           # TypeScript implementation
                    ├── search-conversations
                    ├── index-conversations
                    └── src/
```

## Configuration

### Vim

Key settings from `vimrc`:
- **Indentation**: 4 spaces, expandtab
- **Line length**: Wrap at 500 characters
- **Colorscheme**: Desert with dark background
- **Leader key**: `,` (comma)

Common shortcuts:
- `,w` - Quick save
- `,<space>` - Disable search highlighting

### Claude Code

Key principles from `CLAUDE.md`:
- **Simplicity first** - Clean, maintainable solutions
- **TDD mandatory** - Write tests before implementation
- **No mocks** - Use real data and APIs
- **Root cause debugging** - Never fix symptoms

Python standards:
- 4-space indentation, 80-char line length
- Type annotations required
- Use `uv` for package management (not pip/poetry)

## Updating

Since dotfiles are symlinked, updates are automatic:

```bash
cd ~/dev/dotfiles
git pull origin main
```

If new dependencies were added to conversation search:
```bash
cd ~/.claude/skills/collaboration/remembering-conversations/tool
npm install
```

## Uninstalling

To remove symlinks and restore backups:

```bash
# Remove symlinks
rm ~/.vimrc
rm -rf ~/.claude

# Restore from most recent backup (if exists)
BACKUP=$(ls -td ~/.dotfiles-backup-* | head -1)
if [ -n "$BACKUP" ]; then
    cp -R "$BACKUP"/* ~/
fi
```

## Troubleshooting

### Conversation search not finding results

1. Verify conversations are indexed:
   ```bash
   ~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --verify
   ```

2. Index manually if needed:
   ```bash
   ~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --cleanup
   ```

### sessionEnd hook not running

1. Check hook is executable:
   ```bash
   ls -l ~/.claude/hooks/sessionEnd
   ```

2. Reinstall if needed:
   ```bash
   ~/.claude/skills/collaboration/remembering-conversations/tool/install-hook
   ```

### Installation failed

Check prerequisites:
```bash
node --version  # Should be v16+
npm --version
```

Run installation with verbose output:
```bash
bash -x ./install.sh
```

## Credits

- **Vim configuration** - Personal customizations
- **Claude Code skills structure** - Inspired by [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent
- **Remembering conversations skill** - Based on [obra/clank](https://github.com/obra/clank)
- **Hybrid approach** - Official Claude Code spec with obra's organizational patterns

## License

My personal dotfiles - use at your own discretion.
