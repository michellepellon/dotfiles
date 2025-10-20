# Browsing Skill

**Category**: automation
**Location**: `.claude/skills/automation/browsing/`

## When It Activates

When you need browser automation:
- Controlling authenticated browser sessions
- Managing multiple tabs
- Filling forms and clicking buttons
- Extracting content from JavaScript-heavy sites
- Web scraping requiring interaction
- Sites that don't work with WebFetch

## What It Does

Provides direct Chrome browser control via DevTools Protocol using the `use_browser` MCP tool.

### Core Capabilities

**Navigation**
- Navigate to URLs
- Wait for elements or text to appear
- Handle dynamic page loading

**Interaction**
- Click elements
- Type text into inputs
- Select dropdown options
- Submit forms

**Extraction**
- Extract content as text, HTML, or markdown
- Get element attributes
- Execute JavaScript for complex extraction

**Export**
- Capture screenshots (full page or specific elements)

**Tab Management**
- List all open tabs
- Create new tabs
- Switch between tabs
- Close tabs

## Implementation

Built on Chrome DevTools Protocol with action-based interface:
- Single MCP tool (`use_browser`)
- Auto-starting Chrome with remote debugging
- Multi-tab support via tab_index parameter
- JavaScript execution in page context

## Prerequisites

Requires Chrome MCP server to be installed and configured in Claude Code MCP settings.

**Note**: This skill provides the knowledge/training for using the MCP tool. The actual MCP server must be installed separately.

## Documentation

- **[SKILL.md](../../.claude/skills/automation/browsing/SKILL.md)** - Complete actions reference
- **[examples.md](../../.claude/skills/automation/browsing/examples.md)** - Comprehensive usage examples
- **[README.md](../../.claude/skills/automation/browsing/README.md)** - Installation and overview

## Quick Examples

### Extract Page Content
```json
{action: "navigate", payload: "https://example.com"}
{action: "await_element", selector: "h1"}
{action: "extract", payload: "text", selector: "h1"}
```

### Fill and Submit Form
```json
{action: "navigate", payload: "https://example.com/login"}
{action: "await_element", selector: "input[name=email]"}
{action: "type", selector: "input[name=email]", payload: "user@example.com"}
{action: "type", selector: "input[name=password]", payload: "password123\n"}
{action: "await_text", payload: "Welcome"}
```

### Multi-Tab Workflow
```json
{action: "list_tabs"}
{action: "click", tab_index: 2, selector: "a.link"}
{action: "await_element", tab_index: 2, selector: ".content"}
{action: "extract", tab_index: 2, payload: "text", selector: ".data"}
```

### Extract Structured Data
```json
{action: "navigate", payload: "https://shop.example.com/products"}
{action: "await_element", selector: ".product-grid"}
{action: "eval", payload: `
  Array.from(document.querySelectorAll('.product')).map(p => ({
    name: p.querySelector('.name').textContent,
    price: p.querySelector('.price').textContent
  }))
`}
```

## Best Practices

1. **Always wait before interaction** - Use `await_element` after navigate
2. **Use specific selectors** - Avoid generic "button" or "div" selectors
3. **Submit forms with \n** - Append newline to auto-submit inputs
4. **Verify selectors first** - Extract HTML to check page structure
5. **Increase timeout for slow pages** - Default is 5000ms

## Common Use Cases

- **Authenticated Sessions**: Control logged-in browser sessions
- **Form Automation**: Fill multi-step forms with validation
- **Web Scraping**: Extract data from JavaScript-rendered pages
- **Price Comparison**: Open multiple stores and compare prices
- **Content Extraction**: Convert pages to markdown/text
- **Screenshot Generation**: Capture visual state of pages

See [examples.md](../../.claude/skills/automation/browsing/examples.md) for detailed patterns including:
- Basic operations (navigate, extract, eval)
- Form automation (login, multi-step, search)
- Web scraping (articles, products, structured data)
- Multi-tab workflows (comparison, cross-reference)
- Dynamic content (AJAX, infinite scroll, modals)
- Advanced patterns (JavaScript evaluation, storage access)

## Comparison with Other Tools

**vs WebFetch**: Use browsing when sites require JavaScript, authentication, or interaction. Use WebFetch for simple static content.

**vs Playwright MCP**: Use browsing for existing sessions and multi-tab management. Use Playwright for fresh isolated instances and PDF generation.
