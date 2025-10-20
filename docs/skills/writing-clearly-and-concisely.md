# Writing Clearly and Concisely

**Category:** writing
**Location:** `.claude/skills/writing/writing-clearly-and-concisely/`

Apply William Strunk Jr.'s *The Elements of Style* (1918) to make all writing clearer, stronger, and more professional.

## What It Does

Provides timeless writing rules for ANY text humans will read:
- **Active voice** over passive
- **Positive form** over negative
- **Specific language** over vague
- **Omit needless words** ruthlessly

## When to Use

**ALL writing for humans:**
- Documentation, README files, technical specs
- Commit messages, PR descriptions
- Error messages, UI copy, help text
- Code comments, reports, explanations

**If a human will read it, it's prose. Apply these rules.**

## Core Principles

### Most Critical Rules

**Rule 10: Use Active Voice**
- ❌ "The bug was fixed by the team"
- ✅ "The team fixed the bug"

**Rule 11: Put Statements in Positive Form**
- ❌ "The feature is not very necessary"
- ✅ "The feature is unnecessary"

**Rule 13: Omit Needless Words**
- ❌ "In my opinion, I think that..."
- ✅ (just make the statement)

**Rule 12: Use Definite, Specific, Concrete Language**
- ❌ "handled appropriately"
- ✅ "logged to stderr"

## Common Rationalizations (Reject These)

| Excuse | Reality |
|--------|---------|
| "Write quickly" → skip editing | Clarity ALWAYS worth the time |
| "Just internal docs" | Internal docs need clarity MORE |
| "Technical writing ≠ prose" | ALL writing for humans is prose |
| "Clarity isn't critical here" | This is NEVER true |

**When you hear these, STOP and apply the rules anyway.**

## Systematic Application

1. **Write** - Get ideas down first
2. **Review for passive voice** - Convert to active (Rule 10)
3. **Review for negative forms** - Convert to positive (Rule 11)
4. **Review for vague language** - Make specific (Rule 12)
5. **Cut ruthlessly** - Remove needless words (Rule 13)
6. **Check word order** - Keep related words together (Rule 16)

**Apply ALL rules systematically. Don't stop after "good enough."**

## Context-Specific Guidance

### Commit Messages
- Subject: Omit needless words, active voice, specific
- ❌ "Added feature that allows users to be able to search"
- ✅ "feat: add history search"

### Error Messages
- Active voice: "File exceeds limit" not "limit was exceeded"
- Specific: "File exceeds 10MB limit" not "file is too large"

### Code Comments
- Explain WHY, not WHAT
- ❌ "// This variable stores a cache for performance reasons"
- ✅ "// Cache for performance"

## Under Pressure

Time pressure doesn't justify skipping rules.

**Why:**
- Bad writing wastes EVERY reader's time
- Editing takes 30 seconds
- Reading bad docs wastes minutes per person
- Multiply by number of readers → always worth it

**When told "write quickly":**
1. Write the draft
2. Apply rules
3. Deliver clear result

Don't ask permission to edit. Just do it.

## Files

- **SKILL.md** - Complete specification with all 18 rules
- **elements-of-style.md** - Full reference text (~12,000 tokens)

## Low Context Strategy

When tokens are limited:
1. Write your draft
2. Dispatch subagent with draft + `elements-of-style.md`
3. Have subagent copyedit and return revision

## All Rules Summary

### Elementary Rules of Usage (Grammar)
1-7: Grammar and punctuation rules

### Elementary Principles of Composition
8. One paragraph per topic
9. Begin paragraph with topic sentence
10. **Use active voice**
11. **Put statements in positive form**
12. **Use definite, specific, concrete language**
13. **Omit needless words**
14. Avoid succession of loose sentences
15. Express co-ordinate ideas in similar form
16. **Keep related words together**
17. Keep to one tense in summaries
18. **Place emphatic words at end of sentence**

### Section V
Words and expressions commonly misused (alphabetical reference)

## Testing

Skill validated through TDD workflow with 6 pressure scenarios:
- ✅ Passive voice recognition
- ✅ Systematic rule application
- ✅ Context recognition (commits, errors)
- ✅ Resistance to time pressure
- ✅ Resistance to "clarity isn't critical"
- ✅ Error message clarity

**Test Results**: 5/6 PASS (significantly improved from 2/6 baseline)

See `.claude/skills/meta/creating-skills/tests/` for complete test suite.

## Related

- [Creating Skills](creating-skills.md) - TDD workflow used to create this skill
- [Test-Driven Development](test-driven-development.md) - Core TDD methodology
