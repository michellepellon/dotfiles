# Claude Code Skills

Comprehensive skills that activate automatically based on task context.

## Available Skills

| Skill | Category | Documentation |
|-------|----------|---------------|
| **[Brainstorming](brainstorming.md)** | collaboration | Refine rough ideas into validated designs |
| **[Browsing](browsing.md)** | automation | Chrome browser control via DevTools Protocol |
| **[Creating Skills](creating-skills.md)** | meta | TDD for process documentation |
| **[Executing Plans](executing-plans.md)** | collaboration | Execute plans in controlled batches with checkpoints |
| **[M365 Cost Management](m365-cost-management.md)** | cost analysis | Analyze M365 license costs and utilization |
| **[PDF](pdf.md)** | documents | PDF manipulation toolkit |
| **[Quick Descriptive Stats](quick-descriptive-stats.md)** | analysis | Automatic CSV analysis |
| **[Remembering Conversations](remembering-conversations.md)** | collaboration | Semantic conversation search |
| **[Simplifying Control Flow](simplifying-control-flow.md)** | coding | Flatten nested conditionals, keep nesting < 3 |
| **[Test-Driven Development](test-driven-development.md)** | coding | TDD workflow enforcement |
| **[Writing Clearly and Concisely](writing-clearly-and-concisely.md)** | writing | Apply Strunk's Elements of Style |
| **[Excel/XLSX](xlsx.md)** | documents | Excel spreadsheet operations |

## Architecture

Skills follow Anthropic's official specification with enhancements:

**Official Claude Code spec:**
- Flat directory structure (all skills at `.claude/skills/{skill-name}/`)
- YAML frontmatter (name, description, allowed-tools)
- Automatic activation based on task context
- Progressive disclosure (metadata → SKILL.md → supporting files)

**Enhancements:**
- `when_to_use` frontmatter for improved discovery
- `version` frontmatter for tracking evolution
- Supporting documentation (examples.md, reference.md, README.md)
- Announcement patterns for transparency

## Documentation Structure

Each skill provides:
- **SKILL.md** - Official specification with actions reference
- **README.md** - Installation and quick start
- **examples.md** - Usage examples and patterns
- **reference.md** - Detailed API documentation (where applicable)
- **templates/** - Code templates (where applicable)

## Adding New Skills

1. Create skill directory at `.claude/skills/{skill-name}/`
2. Follow TDD workflow - write tests first (see [Creating Skills](creating-skills.md))
3. Use official spec frontmatter format (name must match directory)
4. Provide progressive disclosure documentation (SKILL.md, examples.md, reference.md)
5. Add announcement pattern: `**Announce at start:** "I'm using the {skill-name} skill to {action}."`
6. Add entry to this table and root README.md

See [Creating Skills](creating-skills.md) for complete TDD workflow and testing methodology.

See [claude-code-setup.md](../claude-code-setup.md) for configuration details.
