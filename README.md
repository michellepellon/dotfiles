# Dotfiles

Personal development environment with Vim, Claude Code skills, and conversation memory.

## Features

- **[Vim](docs/vim-configuration.md)** - Desert colorscheme, smart indentation, shortcuts
- **[Claude Code](docs/claude-code-setup.md)** - TDD workflow, coding standards, skills system
- **[Skills](docs/skills/)** - Design brainstorming, automatic TDD, conversation search, data analysis, browser automation, document processing, clear writing

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
| **[Brainstorming](docs/skills/brainstorming.md)** | collaboration | Before implementation | Refine rough ideas into validated designs through structured questioning |
| **[Browsing](docs/skills/browsing.md)** | automation | Browser automation needed | Chrome control via DevTools Protocol for authenticated sessions |
| **[Creating Skills](docs/skills/creating-skills.md)** | meta | Creating new skills | TDD for process documentation - test with subagents before writing |
| **[Executing Plans](docs/skills/executing-plans.md)** | collaboration | Implementation plan provided | Execute plans in controlled batches with review checkpoints |
| **[M365 Cost Management](docs/skills/m365-cost-management.md)** | cost analysis | Optimizing SaaS spending | Analyze M365 license costs, identify inactive users, track utilization |
| **[PDF](docs/skills/pdf.md)** | documents | PDF processing needed | Extract text/tables, create, merge, split, fill forms |
| **[Quick Descriptive Stats](docs/skills/quick-descriptive-stats.md)** | analysis | CSV uploaded | Automatic statistics, correlations, visualizations |
| **[Remembering Conversations](docs/skills/remembering-conversations.md)** | collaboration | Past context needed | Semantic search of archived conversations |
| **[Simplifying Control Flow](docs/skills/simplifying-control-flow.md)** | coding | Writing conditionals | Flatten nested ifs, keep nesting < 3 levels |
| **[Test-Driven Development](docs/skills/test-driven-development.md)** | coding | All coding tasks | Enforces TDD workflow, requires unit/integration/e2e tests |
| **[Writing Clearly and Concisely](docs/skills/writing-clearly-and-concisely.md)** | writing | Writing/editing text | Apply Strunk's rules - active voice, omit needless words |
| **[Excel/XLSX](docs/skills/xlsx.md)** | documents | Excel/spreadsheet work needed | Data analysis, formulas, formatting, financial models |

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
