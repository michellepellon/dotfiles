# Remembering Conversations Skill

**Category**: collaboration
**Location**: `.claude/skills/collaboration/remembering-conversations/`

## When It Activates

When you mention:
- "We discussed this before"
- Need to find past decisions or patterns
- Debugging similar issues from previous sessions
- Looking for specific git SHAs or error messages
- Need architectural context from past work

## What It Does

Provides semantic and text search of all past Claude Code conversations:

### Semantic Search
Uses vector embeddings (all-MiniLM-L6-v2) to find conceptually similar conversations.

Example:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations "React Router auth errors"
```

### Text Search
Exact text matching for git SHAs, error messages, specific terms.

Example:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --text "a1b2c3d4"
```

### Automatic Archiving
SessionEnd hook automatically archives and indexes every conversation after each session.

## Implementation

- **TypeScript** - Full implementation with 29 files
- **SQLite + sqlite-vec** - Local vector database
- **Node.js dependencies** - Installed automatically via install.sh
- **Subagent pattern** - 50-100x context savings for in-session searches

## Documentation

- **[SKILL.md](../../.claude/skills/collaboration/remembering-conversations/SKILL.md)** - Official specification
- **[INDEXING.md](../../.claude/skills/collaboration/remembering-conversations/INDEXING.md)** - Index management
- **[DEPLOYMENT.md](../../.claude/skills/collaboration/remembering-conversations/DEPLOYMENT.md)** - Setup details

## Search Examples

Time-range filtering:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --after 2025-09-01 "refactoring"
```

View all options:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --help
```

## Manual Operations

Index all unprocessed conversations:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --cleanup
```

Verify index health:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --verify
```

Fix issues:
```bash
~/.claude/skills/collaboration/remembering-conversations/tool/index-conversations --repair
```

See [INDEXING.md](../../.claude/skills/collaboration/remembering-conversations/INDEXING.md) for complete index management guide.
