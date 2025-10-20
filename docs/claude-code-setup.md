# Claude Code Setup

Deep dive into Claude Code configuration, commands, and skills system.

## Overview

The Claude Code configuration provides:
- **Global instructions** via `CLAUDE.md` defining coding standards and TDD workflow
- **Slash commands** for common development tasks
- **Skills system** with automatic activation based on task type
- **Conversation memory** with semantic search capabilities

## File Structure

```
~/.claude/
├── CLAUDE.md                # Global coding standards
├── commands/                # Slash commands
│   ├── brainstorm.md
│   ├── plan.md
│   ├── session-summary.md
│   └── setup.md
├── skills/                  # Claude Code skills
│   ├── testing/
│   ├── collaboration/
│   └── analysis/
└── hooks/
    └── sessionEnd           # Auto-archive conversations
```

## CLAUDE.md Configuration

**Location**: `~/.claude/CLAUDE.md`
**Source**: `~/dev/dotfiles/.claude/CLAUDE.md`

Global instructions that define:

### 1. Working Relationship
- Colleague-based collaboration (no hierarchy)
- Requirement to speak up on technical concerns
- No sycophantic language
- Ask for clarification vs making assumptions

### 2. Code Principles
- **Simplicity first**: Clean, maintainable solutions
- **Readability**: Over conciseness or performance
- **Minimal changes**: Smallest reasonable modifications
- **Consistency**: Match existing style

### 3. Python Standards
- 4-space indentation, 80-character line limit
- Type annotations required throughout
- Use `uv` for package management (not pip/poetry)
- Ordered imports: stdlib → third-party → local

### 4. Version Control
- **Branching**: Descriptive names for each task
- **Commits**: Frequent, one logical change per commit
- **Format**: `<type>: <description> [AI]`
- **Types**: feat, fix, docs, style, refactor, test, chore

### 5. Testing Requirements
- **NO EXCEPTIONS**: Unit, integration, and e2e tests required
- **TDD workflow**: Write tests before implementation
- **No mocks**: Use real data and APIs
- **Pristine output**: Tests must pass cleanly

### 6. Debugging Process
- Phase 1: Root cause investigation
- Phase 2: Hypothesis formation
- Phase 3: Systematic testing
- Phase 4: Solution implementation

See full details in source file.

## Slash Commands

Available via `/command-name` in Claude Code sessions.

### /brainstorm
Interactive spec development through questionnaires.

**Use when**: Starting new features or projects

### /plan
Create multi-level project plans from specs.

**Use when**: Breaking down complex implementations

### /session-summary
Generate timestamped session reports.

**Use when**: Ending work sessions for documentation

### /setup
Validate Claude configuration exists.

**Use when**: Verifying installation

## Skills System

Skills activate automatically based on task context. See [skills documentation](skills/) for detailed information on each skill.

### Categorical Organization

**testing/** - TDD workflow and test requirements
**collaboration/** - Memory and conversation management
**analysis/** - Data analysis and statistics

### Progressive Disclosure

Each skill follows this pattern:
- **SKILL.md** - Official spec (name, description, allowed-tools)
- **examples.md** - Usage examples
- **reference.md** - Detailed API documentation
- **README.md** - Installation and quick start

This keeps CLAUDE.md concise while providing deep-dive documentation where needed.

## SessionEnd Hook

**Location**: `~/.claude/hooks/sessionEnd`
**Source**: `.claude/skills/collaboration/remembering-conversations/tool/install-hook`

Automatically runs after each Claude Code session to:
- Archive conversation JSON
- Generate AI-powered summary (50-120 words)
- Index conversation for semantic search
- Store in SQLite database with vector embeddings

No manual intervention required - conversations are searchable immediately.

## Hybrid Approach

This configuration uses a hybrid methodology:

**From Anthropic's official spec:**
- Minimalist frontmatter (name, description, allowed-tools)
- Official skill structure and activation patterns

**From obra's superpowers:**
- Categorical organization (testing/, collaboration/, analysis/)
- Progressive disclosure to minimize duplication
- Comprehensive supporting documentation
- Sophisticated tooling (semantic search, TypeScript implementations)

Result: Production-grade skills that combine proven organizational patterns with official platform compliance.

## Customization

### Modifying Standards

Edit the source file:
```bash
vim ~/dev/dotfiles/.claude/CLAUDE.md
```

Changes propagate via symlink - no reload needed.

### Adding Commands

Create new command in:
```bash
~/dev/dotfiles/.claude/commands/your-command.md
```

Available immediately as `/your-command`.

### Adding Skills

See individual skill documentation in [docs/skills/](skills/) for development patterns and TDD workflow.
