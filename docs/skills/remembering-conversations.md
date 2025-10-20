# Remembering Conversations

**Category**: collaboration
**Location**: `.claude/skills/collaboration/remembering-conversations/`

## Overview

Search previous Claude Code conversations using semantic or text search. Automatically archives all conversations with AI-powered summaries.

## When It Activates

- "We discussed this before"
- Need past decisions or patterns
- Debugging similar issues
- Looking for git SHAs or error messages
- Need architectural context

## Features

- **Semantic search** - Vector embeddings for concept matching
- **Text search** - Exact matching for SHAs, errors
- **Automatic archiving** - SessionEnd hook indexes conversations
- **Time filtering** - Search by date range
- **Subagent pattern** - 50-100x context savings

## Quick Start

```bash
# Semantic search
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations "auth errors"

# Text search
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --text "a1b2c3d"

# Time range
~/.claude/skills/collaboration/remembering-conversations/tool/search-conversations --after 2025-09-01 "refactoring"
```

## Documentation

See skill files for complete details:
- **[SKILL.md](../../.claude/skills/collaboration/remembering-conversations/SKILL.md)** - Official spec
- **[INDEXING.md](../../.claude/skills/collaboration/remembering-conversations/INDEXING.md)** - Index management
- **[DEPLOYMENT.md](../../.claude/skills/collaboration/remembering-conversations/DEPLOYMENT.md)** - Setup details
