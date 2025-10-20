# Claude Code Skills

Comprehensive skills that activate automatically based on task context.

## Available Skills

| Skill | Category | Documentation |
|-------|----------|---------------|
| **[Test-Driven Development](test-driven-development.md)** | coding | TDD workflow enforcement |
| **[Simplifying Control Flow](simplifying-control-flow.md)** | coding | Flatten nested conditionals, keep nesting < 3 |
| **[Remembering Conversations](remembering-conversations.md)** | collaboration | Semantic conversation search |
| **[Quick Descriptive Stats](quick-descriptive-stats.md)** | analysis | Automatic CSV analysis |
| **[Browsing](browsing.md)** | automation | Chrome browser control |
| **[PDF](pdf.md)** | documents | PDF manipulation toolkit |
| **[Excel/XLSX](xlsx.md)** | documents | Excel spreadsheet operations |
| **[Writing Clearly and Concisely](writing-clearly-and-concisely.md)** | writing | Apply Strunk's Elements of Style |
| **[Creating Skills](creating-skills.md)** | meta | TDD for process documentation |

## Architecture

Skills use a hybrid approach:

**Official Claude Code spec:**
- Minimalist frontmatter (name, description, allowed-tools)
- Automatic activation based on task context

**Obra's organizational patterns:**
- Categorical organization (testing/, collaboration/, analysis/, automation/, documents/)
- Progressive disclosure documentation
- Comprehensive tooling and examples

## Documentation Structure

Each skill provides:
- **SKILL.md** - Official specification with actions reference
- **README.md** - Installation and quick start
- **examples.md** - Usage examples and patterns
- **reference.md** - Detailed API documentation (where applicable)
- **templates/** - Code templates (where applicable)

## Adding New Skills

1. Choose appropriate category (coding/, collaboration/, analysis/, automation/, documents/, writing/, meta/)
2. Follow TDD workflow - write tests first (see [Creating Skills](creating-skills.md))
3. Use official spec frontmatter format
4. Provide progressive disclosure documentation
5. Add entry to this table

See [Creating Skills](creating-skills.md) for complete TDD workflow and testing methodology.

See [claude-code-setup.md](../claude-code-setup.md) for configuration details.
