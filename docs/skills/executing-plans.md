# Executing Plans Skill

**Category**: collaboration
**Location**: `.claude/skills/executing-plans/`

## Overview

Execute implementation plans in controlled batches with review checkpoints - prevents continuous execution, enforces verification steps, stops at blockers.

## Activation

Activates automatically when:
- Michelle provides a complete implementation plan to execute
- You have a written plan with multiple tasks
- Implementing a step-by-step implementation guide
- Plan says "execute this"
- You're tempted to implement everything at once without checkpoints

## The Iron Law

```
NO CONTINUOUS EXECUTION WITHOUT CHECKPOINTS
```

Execute plan without batching? Delete implemented tasks. Start over with batches.

**No exceptions:**
- Don't "execute everything then show Michelle"
- Don't "batch verification at the end"
- Don't "finish quickly then ask for feedback"
- Batch means batch

## The Process

### Step 1: Load and Review Plan

1. Read plan file completely
2. Review critically for clarity, dependencies, conflicts
3. **If concerns**: Raise with Michelle BEFORE starting
4. **If TDD conflict**: Ask how to handle (plan vs. TDD-first)
5. **If no concerns**: Create TodoWrite with all tasks, proceed

### Step 2: Execute Batch

**Default batch size: First 3 tasks**

For each task in batch:
1. Mark as `in_progress` in TodoWrite
2. Follow each step EXACTLY (don't improvise)
3. Run verification as specified (pytest, curl, manual check)
4. **If verification fails**: STOP, report failure, don't continue
5. Mark as `completed` in TodoWrite

**After batch complete**: Proceed to Step 3 (STOP, don't continue)

### Step 3: Report and Wait

When batch complete:
- Show what was implemented (file changes, code)
- Show verification output (test results, command output)
- Say: "Ready for feedback on this batch."
- **WAIT for Michelle's response**

**Do NOT:**
- Continue to next batch without feedback
- Ask "should I continue?" (implies you might anyway)
- Execute next batch "while waiting"

### Step 4: Apply Feedback and Continue

Based on Michelle's feedback:
- Apply requested changes to completed batch
- Address concerns raised
- Execute next batch (return to Step 2)
- Repeat until all tasks complete

### Step 5: Complete Development

After all tasks complete and verified:
- If real feature (not test/demo), commit per git rules
- Present final summary
- Confirm all verifications passed

## When to STOP and Ask

**STOP executing immediately when:**
- Verification fails (test fails, errors, manual check reveals issues)
- Hit blocker mid-batch (missing dependency, unclear instruction)
- Plan has critical gaps preventing implementation
- You don't understand an instruction
- Repeated failures on same task (3+ attempts)

**Ask for clarification rather than guessing.**

## Batch Size Guidelines

**Default: 3 tasks**

**Adjust to 1-2 tasks when:**
- Tasks are complex or unclear
- Time pressure (smaller batches fail faster)
- Early in plan (establish pattern)
- Previous batch had issues

**Adjust to 4-5 tasks when:**
- Tasks are trivial or mechanical
- Pattern is established and working
- Michelle explicitly requests larger batches

**Never execute 6+ tasks without checkpoint unless explicitly authorized.**

## Common Rationalizations (Don't Accept)

| Excuse | Reality |
|--------|---------|
| "Faster to execute all at once" | Batches catch issues early, prevent wasted work |
| "Checkpoints slow me down" | Checkpoints save time via course correction |
| "Verification steps are optional" | Verification is required if plan specifies it |
| "I'll just implement the missing piece" | STOP and ask - you don't know Michelle's intent |
| "Time pressure means skip checkpoints" | Time pressure = SMALLER batches, not skipping |
| "I know what's needed" | You don't - ask anyway |

## Red Flags - STOP and Start Over

**If you find yourself:**
- Implementing tasks 4, 5, 6 without having reported on 1-3
- Skipping verification steps "temporarily"
- Thinking "I'll ask Michelle after I finish"
- Creating missing files/modules without asking
- Continuing past test failures
- Working "while waiting" for feedback

**All of these mean: STOP. Report current batch. Wait for feedback.**

## Integration with Michelle's Rules

### TDD Conflict
- If plan is implementation-first but Michelle requires TDD, STOP and ask
- Don't assume plan overrides Michelle's rules
- Don't assume Michelle's rules override plan
- Ask explicitly

### Git Requirements
- Follow Michelle's git rules for commits
- If plan doesn't mention git but code is non-trivial, apply git rules
- Batch completion = good commit checkpoint

### Time Pressure
- Michelle's RULE #1 still applies: get permission for exceptions
- Time pressure = smaller batches (1-2 tasks), not skipping steps
- Ask: "Should I adjust batch size or skip any verifications?"

## Key Principles

- **Review plan critically FIRST** - raise concerns before starting
- **Execute in batches** - default 3 tasks
- **Run verifications as specified** - don't skip
- **STOP at blockers** - don't guess
- **Report and WAIT between batches** - no continuous execution
- **Time pressure = smaller batches** - not skipping checkpoints
- **Ask about conflicts** - with Michelle's rules
- **Mark tasks in TodoWrite** - track progress

**The goal is correct implementation, not fast implementation.**

## Documentation

- **[SKILL.md](../../.claude/skills/executing-plans/SKILL.md)** - Complete specification

## See Also

- [Brainstorming](brainstorming.md) - For design before implementation
- [Test-Driven Development](test-driven-development.md) - TDD workflow
- [Writing Clearly and Concisely](writing-clearly-and-concisely.md) - For clear plans
