# Browsing

**Category**: automation
**Location**: `.claude/skills/automation/browsing/`

## Overview

Control Chrome browser directly via DevTools Protocol using the `use_browser` MCP tool for web automation, scraping, and interaction.

## When It Activates

- Browser automation needed
- Form filling and interaction
- Web scraping (JavaScript-heavy sites)
- Authenticated browser sessions
- Multi-tab workflows

## Features

- **Navigation** - Navigate, wait for elements, handle dynamic loading
- **Interaction** - Click, type, select dropdowns, submit forms
- **Extraction** - Text, HTML, markdown, attributes, JavaScript execution
- **Export** - Full page or element screenshots
- **Tab management** - List, create, switch, close tabs

## Prerequisites

Requires Chrome MCP server (installed automatically via install.sh).

**Manual MCP configuration**:
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

## Quick Examples

**Navigate and extract**:
```json
{action: "navigate", payload: "https://example.com"}
{action: "await_element", selector: "h1"}
{action: "extract", payload: "text", selector: "h1"}
```

**Fill and submit form**:
```json
{action: "type", selector: "input[name=email]", payload: "user@example.com"}
{action: "type", selector: "input[name=password]", payload: "pass123\n"}
{action: "await_text", payload: "Welcome"}
```

## Documentation

See skill files for complete details:
- **[SKILL.md](../../.claude/skills/automation/browsing/SKILL.md)** - Actions reference and best practices
- **[examples.md](../../.claude/skills/automation/browsing/examples.md)** - Comprehensive usage patterns
- **[README.md](../../.claude/skills/automation/browsing/README.md)** - Installation and overview
