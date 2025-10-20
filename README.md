# Dotfiles

Personal development environment with Vim, Claude Code skills, and conversation memory.

## Features

- **[Vim](docs/vim-configuration.md)** - Desert colorscheme, smart indentation, shortcuts
- **[Claude Code](docs/claude-code-setup.md)** - TDD workflow, coding standards, skills system
- **[Skills](docs/skills/)** - Automatic TDD, conversation search, data analysis, browser automation

## Quick Start

### Prerequisites

- Node.js v16+ ([install](https://nodejs.org) or use [nvm](https://github.com/nvm-sh/nvm))
- git

### Installation

```bash
git clone https://github.com/michellepellon/dotfiles.git ~/dev/dotfiles
cd ~/dev/dotfiles
./install.sh
```

The installer automatically:
- Backs up existing files
- Creates symlinks to `~/.vimrc` and `~/.claude/`
- Installs dependencies (conversation search, Chrome MCP)
- Configures MCP for Claude Code CLI and Desktop

### Post-Install

```bash
source ~/.bashrc  # or ~/.zshrc
```

Restart Claude Code to load MCP configuration.

## Claude Code Skills

Skills activate automatically based on task context. [See all details →](docs/skills/)

| Skill | Category | Activates When | What It Does |
|-------|----------|----------------|--------------|
| **[Test-Driven Development](docs/skills/test-driven-development.md)** | testing | All coding tasks | Enforces TDD workflow, requires unit/integration/e2e tests |
| **[Remembering Conversations](docs/skills/remembering-conversations.md)** | collaboration | Past context needed | Semantic search of archived conversations |
| **[Quick Descriptive Stats](docs/skills/quick-descriptive-stats.md)** | analysis | CSV uploaded | Automatic statistics, correlations, visualizations |
| **[Browsing](docs/skills/browsing.md)** | automation | Browser automation needed | Chrome control via DevTools Protocol |

## Documentation

- **[Vim Configuration](docs/vim-configuration.md)** - Keybindings, settings, customization
- **[Claude Code Setup](docs/claude-code-setup.md)** - CLAUDE.md, commands, hooks, MCP
- **[Skills System](docs/skills/)** - Detailed skill documentation

## Common Tasks

### Update

```bash
cd ~/dev/dotfiles
git pull origin main
```

Changes apply immediately via symlinks.

## Troubleshooting

<details>
<summary>Conversation search not working</summary>

```bash
# Verify index
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --verify

# Rebuild
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --cleanup
```
</details>

<details>
<summary>sessionEnd hook not running</summary>

```bash
# Check executable
ls -l ~/.claude/hooks/sessionEnd

# Reinstall
~/.claude/skills/collaboration/remembering-conversations/tool/install-hook
```
</details>

<details>
<summary>Installation failed</summary>

```bash
# Check prerequisites
node --version  # Should be v16+
npm --version

# Verbose output
bash -x ./install.sh
```
</details>

<details>
<summary>MCP configuration not working</summary>

Automatic configuration targets:
- **CLI**: `~/.claude.json`
- **Desktop** (macOS): `~/Library/Application Support/Claude/claude_desktop_config.json`

Manual configuration:
```json
{
  "mcpServers": {
    "chrome": {
      "command": "node",
      "args": ["~/.claude/mcp/chrome/dist/index.js"]
    }
  }
}
```

Restart Claude after configuring.
</details>

## Credits

- **Skills** - Inspired by [obra/superpowers](https://github.com/obra/superpowers)
- **Conversation memory** - Based on [obra/clank](https://github.com/obra/clank)
- **Browser automation** - Based on [obra/superpowers-chrome](https://github.com/obra/superpowers-chrome)
- **Approach** - Official Claude Code spec + obra's patterns

## License

Personal dotfiles - use at your own discretion.
