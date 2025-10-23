# Brainstorming

Transform rough ideas into fully-formed designs through structured Socratic questioning.

## Overview

The brainstorming skill helps refine vague ideas ("add user authentication") into concrete, validated designs before writing any code. It uses structured questioning, alternative exploration, and incremental validation across six phases.

## When to Use

- **Before implementation**: User has rough idea that needs refinement
- **Architecture decisions**: Multiple approaches possible, need to explore
- **Unclear requirements**: Requirements incomplete or ambiguous
- **Design validation**: Need to validate approach before coding

## How It Works

The skill guides you through six phases:

1. **Understanding** - Ask questions one at a time to gather purpose, constraints, criteria
2. **Exploration** - Propose 2-3 approaches with trade-offs
3. **Design Presentation** - Present design in sections, validate incrementally
4. **Design Documentation** - Write design to `docs/plans/` using clear writing
5. **Worktree Setup** - Create isolated workspace (if implementing)
6. **Planning Handoff** - Create implementation plan (if implementing)

## Key Features

### Structured Questioning

**AskUserQuestion tool for choices:**
- Phase 1: Clarifying questions (storage location, auth method, etc.)
- Phase 2: Architectural approaches (2-3 alternatives with trade-offs)

**Open-ended for validation:**
- Phase 3: "Does this look right so far?"
- Getting detailed feedback

### Flexible Progression

Go backward when needed:
- New constraint revealed → Return to Phase 1
- Partner questions approach → Return to Phase 2
- Requirements unclear → Return to Phase 1

**Flexibility over rigidity** - don't force forward linearly.

### Integration with Other Skills

- **Phase 4**: Uses writing-clearly-and-concisely for documentation quality
- **Phase 5**: Uses using-git-worktrees for workspace setup
- **Phase 6**: Uses writing-plans for implementation breakdown

## Example Session

```
User: "I want to add user authentication"

Agent: I am using the brainstorming skill to refine your idea.

Agent: [Uses AskUserQuestion]
  Where should authentication data be stored?
  - Session storage (secure, re-login required)
  - Local storage (persistent, convenient)
  - Cookies (SSR-compatible)

User: Local storage

Agent: What authentication method?
  [Presents OAuth, email/password, magic links, MFA with trade-offs]

User: OAuth

Agent: What backend framework are you using?

User: Express.js with MongoDB

Agent: [Proposes 3 architectural approaches]
  - Passport.js with OAuth strategies
  - Custom OAuth flow
  - Auth0 managed service

User: Passport.js

Agent: Here's the architecture design...
  [Presents in sections, validates each]

Agent: Writing design to docs/plans/2025-10-23-oauth-authentication-design.md

Agent: Ready to create implementation plan?
```

## Real-World Impact

**Without brainstorming:**
- Start coding with vague requirements
- Discover constraints mid-implementation
- Refactor/rewrite when approach doesn't fit

**With brainstorming:**
- Validated design before first line of code
- Constraints surfaced early
- Clear implementation path

## Files

- **.claude/skills/brainstorming/SKILL.md** - Core workflow specification
- **.claude/skills/brainstorming/examples.md** - Complete session examples
- **.claude/skills/brainstorming/templates/progress-checklist.md** - Track phases

## Principles

| Principle | Application |
|-----------|-------------|
| **One question at a time** | Phase 1: Single question per message |
| **Structured choices** | Use AskUserQuestion for 2-4 options with trade-offs |
| **YAGNI ruthlessly** | Remove unnecessary features from all designs |
| **Explore alternatives** | Always propose 2-3 approaches |
| **Incremental validation** | Present design in sections, validate each |
| **Flexible progression** | Go backward when needed |
| **Announce usage** | State skill usage at start |

## When NOT to Use

- Trivial changes (adding a console.log)
- Complete spec already provided
- Obvious implementation (no design needed)

If requirements are crystal clear and implementation is straightforward, skip brainstorming and proceed directly.

## See Also

- [Test-Driven Development](test-driven-development.md) - Required after design phase
- [Writing Clearly and Concisely](writing-clearly-and-concisely.md) - Used in Phase 4
- [Creating Skills](creating-skills.md) - TDD workflow for documentation
