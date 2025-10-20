# Quick Descriptive Stats

**Category**: analysis
**Location**: `.claude/skills/analysis/quick-descriptive-stats/`

## Overview

Proactively analyzes CSV files without asking questions. Generates comprehensive statistics, correlations, and adaptive visualizations.

## When It Activates

When CSV files are uploaded or tabular data analysis is requested.

## Features

- **Statistics** - Mean, median, std dev, quartiles, correlations
- **Data quality** - Missing value detection
- **Visualizations** - Heatmaps, distributions, time-series, categorical plots
- **Adaptive** - Adjusts based on data types detected

## Installation

Requires Python dependencies:

```bash
cd ~/.claude/skills/analysis/quick-descriptive-stats
pip3 install -r requirements.txt
```

Or using uv:
```bash
uv sync
```

## Code Quality

- 476 lines (11 modular functions)
- 200+ lines of tests (16 tests)
- Full type annotations
- 80-char line compliance

## Documentation

See skill files for complete details:
- **[SKILL.md](../../.claude/skills/analysis/quick-descriptive-stats/SKILL.md)** - Official spec
- **[README.md](../../.claude/skills/analysis/quick-descriptive-stats/README.md)** - Installation
- **[examples.md](../../.claude/skills/analysis/quick-descriptive-stats/examples.md)** - Usage examples
- **[reference.md](../../.claude/skills/analysis/quick-descriptive-stats/reference.md)** - API reference
