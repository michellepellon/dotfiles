# Test-Driven Development Skill

**Category**: testing
**Location**: `.claude/skills/testing/test-driven-development/`

## When It Activates

All coding tasks including:
- Implementing new features
- Fixing bugs
- Refactoring code

Activates automatically unless explicitly authorized to skip testing.

## What It Does

Enforces strict TDD workflow:
1. Write failing test defining desired functionality
2. Run test to confirm expected failure
3. Write ONLY enough code to make test pass
4. Run test to confirm success
5. Refactor while ensuring tests remain green
6. Repeat

## Key Requirements

- **Comprehensive coverage**: Unit, integration, and end-to-end tests
- **No mocks**: Use real data and APIs
- **Pristine output**: Test output must be clean to pass
- **Test-first**: Always write tests before implementation

## Documentation

- **[SKILL.md](../../.claude/skills/testing/test-driven-development/SKILL.md)** - Official specification
- **[examples.md](../../.claude/skills/testing/test-driven-development/examples.md)** - Workflow examples
- **[reference.md](../../.claude/skills/testing/test-driven-development/reference.md)** - Detailed methodology
- **[templates/](../../.claude/skills/testing/test-driven-development/templates/)** - Test templates

## Quick Start

No installation required - skill activates automatically during coding tasks.

See [examples.md](../../.claude/skills/testing/test-driven-development/examples.md) for complete TDD workflow examples.
