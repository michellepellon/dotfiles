# CLAUDE.md
*Last Updated 2025-05-12*

> **purpose** - This file is the 

## 0. Interaction

- Anytime you interact with me, you MUST address me as "Michelle".

## 1. Development Philosophy

- **Simplicity**: We prefer simple, clean, maintainable solutions over clever 
or complex ones, even if the latter are more concise or performant. 

- **Readability**: Readability and maintainability are primary concerns.

- **Minimal Changes**: Make the smallest reasonable changes to get to the 
desired outcome. You MUST ask permission before reimplementing features or 
systems from scratch instead of updating the existing implementation.

- **Clean Logic**: When modifying code, match the style and formatting of 
surrounding code, even if it differs from standard style guides. 
Consistency within a file is more important than strict adherence to external 
standards.

- **Build Iteratively**: NEVER make code changes that are not directly related 
to the task you are currently assigned. If you notice something that should be 
fixed but is unrelated to your current task, document it in a new issue instead 
of fixing it immediately.

- **Comments**: NEVER remove code comments unless you can prove that they are 
actively false. Comments are important documentation and should be preserved 
even if they seem redundant or unncessary to you.

- **TODO Comments**: Mark issues in existing code with "TODO:" prefix.

- **Descriptive Names**: When writing comments, avoid referring to temporal 
context about refactors or recent changes. Comments should be evergreen and 
describe the code as it is, not how it evolved or was recently changed.

- **Build Test Environments**: NEVER implement a mock mode for testing or for 
any purpose. We always use real data and real APIs, never mock implementations.

- **Functional Code**: Use functional and stateless approaches where they
improve clarity.

- **Clean logic**: Keep core logic clean and push implementation details to the 
edges.

- **File Organsiation**: Balance file organization with simplicity - use an 
appropriate number of files for the project scale.

# Getting Help

- ALWAYS ask for clarification rather than making assumptions.
- If you are having trouble with something, it is okay to stop and ask for
help. Especially if it is something your human might be better at.

# Code Style

## Python

- **Indentation**: 4 spaces
- **Line length**: 80 characters
- **Imports**: stdlib -> third-party -> local, alphabetized within groups
- **Naming**: PEP 8 naming; `snake_case` for functions/variables, `CamelCase` 
for classes `UPPER_SNAKE_CASE` for constants
- **Types**: Use type annotations consistently; prefer Union syntax (`str | None`) 
for Python 3.10+
- **Documentation**: Triple-quote docstrings with param/return descriptions
- **Package management**: Use uv for everything (uv add, uv run, etc); do not 
use old fashioned methods for package management like poetry, pip or 
easy_install. Make sure that there is a pyproject.toml file in the root 
directory.
- **Error Handling**: Typed exceptions, and context managers for resources.

# Commit Discipline

- For non-trivial edits, all changes MUST be tracked in git.
- If the project isn't in a git repo, YOU MUST STOP and ask permission to initialize one.
- If there are uncommitted changes or untracked files when starting work, YOU MUST STOP and ask how to handle them. Suggest committing existing work first.
- When starting work without a clear branch for the current task, YOU MUST create a WIP branch.
- YOU MUST commit frequently throughout the development process.
- **Granular commits**: One logical change per commit.
- **Tag AI-generated commits**: e.g., `feat: optimise feed query [AI]`.

## Testing

- Tests MUST comprehensively cover ALL implemented functionality.
- YOU MUST NEVER ignore system or test output - logs and messages often contain CRITICAL information.
- Test output MUST BE PRISTINE TO PASS.
- If logs are expected to contain errors, these MUST be captured and tested.
- NO EXCEPTIONS POLICY: ALL projects MUST have unit tests, integration tests, AND end-to-end tests. The only way to skip any test type is if Michelle EXPLICITLY states: "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME."

## Test-Driven Development (TDD)

We practice strict TDD. This means:

1. YOU MUST write a failing test that defines the desired functionality BEFORE writing implementation code
2. YOU MUST run the test to confirm it fails as expected
3. YOU MUST write ONLY enough code to make the failing test pass
4. YOU MUST run the test to confirm success
5. YOU MUST refactor code while ensuring tests remain green
6. YOU MUST repeat this process for each new feature or bugfix

# Compliance Check

Before submitting any work, verify that you have followed ALL guidelines above.
If you find yourself considering an exception to ANY rule, YOU MUST STOP and
get explicit permission from Michelle first.
