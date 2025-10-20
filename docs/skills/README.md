# Claude Code Skills

Comprehensive skills that activate automatically based on task context.

## Available Skills

### [Test-Driven Development](test-driven-development.md)
**Category**: testing

Enforces strict TDD workflow for all development tasks. Requires comprehensive test coverage (unit, integration, e2e) before writing implementation code.

**Activates**: All coding tasks (features, bug fixes, refactoring)

---

### [Remembering Conversations](remembering-conversations.md)
**Category**: collaboration

Search previous Claude Code conversations using semantic or text search. Automatically archives all conversations after each session with AI-powered summaries.

**Activates**: When past context or decisions are needed

---

### [Quick Descriptive Stats](quick-descriptive-stats.md)
**Category**: analysis

Proactively analyzes CSV files without asking questions. Generates comprehensive statistics, correlations, and adaptive visualizations based on data types.

**Activates**: When CSV files are uploaded or tabular data analysis is requested

---

### [Browsing](browsing.md)
**Category**: automation

Control Chrome browser directly via DevTools Protocol. Navigate, interact, extract content, manage tabs, and execute JavaScript for web automation and scraping.

**Activates**: When browser automation, form filling, or interactive web scraping is needed

---

## Skills Architecture

All skills follow the hybrid approach combining:

**Official Claude Code spec:**
- Minimalist frontmatter (name, description, allowed-tools)
- Automatic activation based on task context

**Obra's organizational patterns:**
- Categorical organization (testing/, collaboration/, analysis/, automation/)
- Progressive disclosure documentation
- Comprehensive tooling and examples

## Documentation Structure

Each skill provides:
- **SKILL.md** - Official specification
- **README.md** - Installation and quick start
- **examples.md** - Usage examples
- **reference.md** - Detailed API documentation
- **templates/** - Code templates (where applicable)

## Adding New Skills

1. Choose appropriate category (testing/, collaboration/, analysis/, automation/, etc.)
2. Follow TDD workflow - write tests first
3. Use official spec frontmatter format
4. Provide progressive disclosure documentation
5. Add overview to this directory

See [claude-code-setup.md](../claude-code-setup.md) for complete configuration details.
