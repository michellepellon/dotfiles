# Creating Skills

**Category:** meta
**Location:** `.claude/skills/meta/creating-skills/`

Test-Driven Development for process documentation. Write pressure scenarios with subagents, watch them fail without the skill, write the skill, watch them pass, then refactor to close loopholes.

## What It Does

Applies TDD methodology to skill creation:
- **RED**: Run scenarios WITHOUT skill - document baseline failures
- **GREEN**: Write minimal skill addressing those failures
- **REFACTOR**: Close loopholes discovered during testing

## When to Use

**Create skills when:**
- Technique wasn't intuitively obvious to you
- You'd reference this again across projects
- Pattern applies broadly (not project-specific)
- Others would benefit from documentation

**Don't create skills for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (use CLAUDE.md instead)

## Core Principle

**If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.**

All skills must be tested before deployment. No exceptions.

## Skill Types

| Type | Description | Examples |
|------|-------------|----------|
| **Technique** | Concrete method with steps | condition-based-waiting, root-cause-tracing |
| **Pattern** | Mental model for problems | flatten-with-flags, test-invariants |
| **Reference** | API/command documentation | office docs, tool references |

## Quick Reference

### Directory Structure

```
.claude/skills/
  category/
    skill-name/
      SKILL.md              # Required
      supporting-file.*     # Optional (tools, heavy reference)
```

### SKILL.md Format

```yaml
---
name: Human-Readable Name
description: One-line summary
when_to_use: Symptoms and situations (critical for discovery)
version: 1.0.0
languages: all | [typescript, python] | etc
dependencies: (optional) Required tools/libraries
---
```

### Testing Workflow

1. **Design pressure scenarios** (time, sunk cost, authority, exhaustion)
2. **Run WITHOUT skill** - capture exact rationalizations
3. **Write minimal skill** - address specific failures
4. **Run WITH skill** - verify compliance
5. **Iterate** - close new loopholes found

## Key Concepts

### Claude Search Optimization (CSO)

Make skills discoverable through:
- **Rich when_to_use**: Include symptoms, error messages, tool names
- **Keyword coverage**: Use synonyms, actual commands, symptoms
- **Descriptive naming**: Active voice, verb-first (creating-skills, not skill-creation)
- **Content repetition**: Mention concepts in multiple sections

### Token Efficiency

Skills load into every conversation. Be concise:
- Getting-started workflows: <150 words
- Frequently-loaded skills: <200 words total
- Other skills: <500 words

### Bulletproofing

For discipline-enforcing skills:
- Close every loophole explicitly
- Address "spirit vs letter" arguments
- Build rationalization tables from test results
- Create red flags lists for self-checking

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip testing "obvious" skills | Test anyway - clear to you ≠ clear to agents |
| Batch create multiple skills | Test each before moving to next |
| Use flowcharts for reference | Use tables/lists instead |
| Multi-language examples | One excellent example beats many mediocre |
| Generic labels (step1, helper2) | Use semantic names |

## Implementation

The skill provides:
- Complete TDD workflow for documentation
- Testing strategies for each skill type
- CSO optimization techniques
- Bulletproofing methods for discipline skills
- Anti-patterns and common rationalizations

See `.claude/skills/meta/creating-skills/SKILL.md` for complete specification.

## Testing

Skills should be tested with subagent pressure scenarios before deployment. This skill itself demonstrates the meta-testing approach it documents.

## Files

- **SKILL.md** - Complete specification with TDD workflow
- **graphviz-conventions.dot** - Flowchart style guide

## Related

- [Test-Driven Development](test-driven-development.md) - Core TDD workflow for code
- [Skills System](README.md) - Architecture and organization
