# Executing Plans Skill

## Overview

Discipline-enforcing skill for implementing plans in controlled batches with review checkpoints. Prevents continuous execution without feedback, enforces verification steps, and stops agents at blockers instead of guessing.

## Files

- **SKILL.md** - Main skill document (1010 words)
  - Iron Law: NO CONTINUOUS EXECUTION WITHOUT CHECKPOINTS
  - 5-step process: Load/Review → Execute Batch → Report/Wait → Continue → Complete
  - Rationalization table with 10 common excuses
  - Red flags for self-checking
  - Integration with Michelle's CLAUDE.md rules

- **test-scenarios.md** - Test scenarios for skill validation (5 scenarios)
- **baseline-results.md** - Baseline behavior WITHOUT skill (RED phase)
- **verification-results.md** - Improved behavior WITH skill (GREEN phase)
- **test-plan.md** - Sample 6-task plan for testing

## Skill Type

**DISCIPLINE** - Enforces behaviors agents don't naturally do and prevents rationalizations under pressure.

## Key Features

### Iron Law
"NO CONTINUOUS EXECUTION WITHOUT CHECKPOINTS" with explicit loophole closures:
- Don't "execute everything then show Michelle"
- Don't "batch verification at the end"
- Don't "finish quickly then ask for feedback"

### 5-Step Process
1. **Load and Review Plan** - Critical review BEFORE starting, check for conflicts
2. **Execute Batch** - Default 3 tasks, run verifications, mark in TodoWrite
3. **Report and Wait** - Show work, show verification, WAIT for feedback
4. **Apply Feedback and Continue** - Iterate based on feedback
5. **Complete Development** - Final summary and verification

### Rationalization Prevention
Addresses 10 common excuses from baseline testing:
- "Faster to execute all at once" → batches catch issues early
- "Checkpoints slow me down" → enable course correction
- "Time pressure means skip checkpoints" → smaller batches instead
- "I'll just implement missing piece" → STOP and ask
- "Demo in 2 hours, no time" → bad demo worse than late demo

### Integration with Michelle's Rules
- Explicitly addresses TDD conflicts (implementation-first plans vs. test-first rules)
- Reinforces RULE #1 (get permission for exceptions)
- Transforms time pressure from "break rules" to "adjust batch size"

## Test Results

### Baseline (WITHOUT Skill)

**With Michelle's strict CLAUDE.md:**
- ✅ Stops to ask questions (good)
- ❌ No batch execution model
- ❌ Would execute all tasks after clarification
- ⚠️ Tempted to skip steps under time pressure (blocked by RULE #1)

**Without strict rules:**
- ❌ Executed all 6 tasks continuously
- ❌ No checkpoints
- ❌ Skipped verification steps
- ❌ Reported only at completion
- ❌ "Silent until completion" approach

### With Skill
- ✅ Critical review before starting
- ✅ Planned 3-task batches with checkpoints
- ✅ Stopped at conflicts to ask for clarification
- ✅ Proposed smaller batches (1-2 tasks) for time pressure
- ✅ Resisted all 10 rationalizations explicitly
- ✅ Referenced specific skill lines to justify approach

## TDD Process Applied

**RED Phase:**
- Created 5 pressure test scenarios
- Ran 3 baseline tests (strict rules, time pressure, permissive)
- Documented exact failures and rationalizations

**GREEN Phase:**
- Wrote discipline skill with Iron Law and rationalization table
- Addressed all baseline failures
- Verified agents comply under pressure

**REFACTOR Phase:**
- No new rationalizations emerged in testing
- Skill appears comprehensive for tested scenarios

## Usage

When Michelle (or any user) provides an implementation plan with multiple tasks, grep will find this skill via keywords:
- "implementation plan"
- "execute this plan"
- "step-by-step guide"
- "multiple tasks"
- "implement everything at once" (symptom)
- "checkpoints"
- "batch execution"

The skill will enforce:
- Batch execution (default 3 tasks)
- Verification steps as specified
- Checkpoint reporting between batches
- Stopping at blockers
- Using TodoWrite for tracking

## Key Principles

1. **Batch execution prevents wasted work** - catch issues early before implementing everything
2. **Checkpoints enable course correction** - feedback prevents wrong direction
3. **Time pressure = smaller batches**, not skipping steps
4. **Ask rather than guess** - especially for missing pieces
5. **Verification is required**, not optional
6. **STOP at blockers** - don't implement missing dependencies yourself

## Word Count

1010 words - appropriate for discipline skill with comprehensive rationalization table.

## CSO Optimization

- ✅ Symptom-rich `when_to_use` (includes "tempted to implement everything at once")
- ✅ Keywords throughout (batches, checkpoints, verification, blockers, continuous execution)
- ✅ Active voice naming ("Executing Plans")
- ✅ Mention key concepts in multiple sections (batches, checkpoints, verification)
