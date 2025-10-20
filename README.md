# Dotfiles

Personal development environment configuration with Vim, Claude Code, and conversation memory.

## Features

- **[Vim Configuration](docs/vim-configuration.md)** - Desert colorscheme, smart indentation, custom shortcuts
- **[Claude Code Setup](docs/claude-code-setup.md)** - TDD workflow, coding standards, slash commands
- **[Skills System](docs/skills/)** - TDD enforcement, conversation search, CSV analysis, browser automation
- **Conversation Memory** - Semantic search of past Claude Code sessions

## Quick Start

### Prerequisites

- Node.js (v16+) - [Install](https://nodejs.org) or use [nvm](https://github.com/nvm-sh/nvm)
- git

### Installation

```bash
git clone https://github.com/michellepellon/dotfiles.git ~/dev/dotfiles
cd ~/dev/dotfiles
./install.sh
```

The installer will:
- Check prerequisites
- Backup existing dotfiles
- Create symlinks to `~/.vimrc` and `~/.claude/`
- Install conversation search dependencies
- Set up automatic conversation archiving

### Post-Install

Restart your terminal or:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## What Gets Installed

### Symlinks

| Source | Target | Description |
|--------|--------|-------------|
| `vimrc` | `~/.vimrc` | Vim configuration |
| `.claude/CLAUDE.md` | `~/.claude/CLAUDE.md` | Global Claude instructions |
| `.claude/commands/` | `~/.claude/commands/` | Slash commands |
| `.claude/skills/` | `~/.claude/skills/` | Claude Code skills |
| `.claude/mcp/` | `~/.claude/mcp/` | MCP servers (Chrome browser automation) |

### Additional Setup

- **Conversation search** - Node.js dependencies installed automatically
- **sessionEnd hook** - Enables automatic conversation archiving
- **Chrome MCP server** - Built automatically for browser automation

## MCP Configuration

To enable browser automation, configure Claude Code to use the Chrome MCP server:

1. Open Claude Code MCP settings
2. Add the Chrome MCP server:

```json
{
  "mcpServers": {
    "chrome": {
      "command": "node",
      "args": [
        "~/.claude/mcp/chrome/dist/index.js"
      ]
    }
  }
}
```

3. Restart Claude Code

The browsing skill will now be able to control Chrome via the `use_browser` MCP tool.

See [docs/skills/browsing.md](docs/skills/browsing.md) for usage examples.

## Documentation

### Configuration
- **[Vim Configuration](docs/vim-configuration.md)** - Deep dive on vimrc settings
- **[Claude Code Setup](docs/claude-code-setup.md)** - CLAUDE.md, commands, hooks

### Skills
- **[All Skills Overview](docs/skills/)** - Complete skills documentation
- **[Test-Driven Development](docs/skills/test-driven-development.md)** - TDD workflow enforcement
- **[Remembering Conversations](docs/skills/remembering-conversations.md)** - Semantic conversation search
- **[Quick Descriptive Stats](docs/skills/quick-descriptive-stats.md)** - Automatic CSV analysis
- **[Browsing](docs/skills/browsing.md)** - Chrome browser automation and web scraping

## Usage

### Vim

```bash
vim myfile.py
```

Configuration loads automatically. See [vim-configuration.md](docs/vim-configuration.md) for shortcuts and customization.

### Claude Code

Claude Code automatically loads `~/.claude/CLAUDE.md` when starting.

#### Slash Commands

- `/brainstorm` - Interactive spec development
- `/plan` - Create project plans from specs
- `/session-summary` - Generate session reports
- `/setup` - Validate configuration

#### Skills

Skills activate automatically based on task context. See [docs/skills/](docs/skills/) for details on each skill.

#### Search Conversations

Semantic search:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations "React Router auth errors"
```

Exact text match:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --text "a1b2c3d4"
```

See [remembering-conversations](docs/skills/remembering-conversations.md) for complete search capabilities.

## Updating

Dotfiles are symlinked - updates apply automatically:

```bash
cd ~/dev/dotfiles
git pull origin main
```

If conversation search dependencies change:
```bash
cd ~/.claude/skills/collaboration/remembering-conversations/tool
npm install
```

## Troubleshooting

### Conversation search not working

```bash
# Verify index
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --verify

# Rebuild index
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --cleanup
```

### sessionEnd hook not running

```bash
# Check hook is executable
ls -l ~/.claude/hooks/sessionEnd

# Reinstall if needed
~/.claude/skills/collaboration/remembering-conversations/tool/install-hook
```

### Installation failed

```bash
# Verify prerequisites
node --version  # Should be v16+
npm --version

# Run with verbose output
bash -x ./install.sh
```

## Credits

- **Vim configuration** - Personal customizations
- **Skills structure** - Inspired by [obra/superpowers](https://github.com/obra/superpowers)
- **Conversation memory** - Based on [obra/clank](https://github.com/obra/clank)
- **Browser automation** - Based on [obra/superpowers-chrome](https://github.com/obra/superpowers-chrome)
- **Hybrid approach** - Official Claude Code spec + obra's organizational patterns

## License

Personal dotfiles - use at your own discretion.
