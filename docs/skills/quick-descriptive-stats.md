# Quick Descriptive Stats Skill

**Category**: analysis
**Location**: `.claude/skills/analysis/quick-descriptive-stats/`

## When It Activates

When a CSV file is uploaded or tabular data analysis is requested.

## What It Does

Proactively analyzes CSV files **without asking questions** - provides immediate, comprehensive analysis.

### Analysis Features

- **Summary statistics**: Mean, median, std dev, quartiles
- **Correlation analysis**: Correlation matrix for numeric columns
- **Data quality checks**: Missing value detection and reporting
- **Adaptive visualizations**: Based on detected data types

### Visualizations Created

- **Correlation heatmap** - For numeric columns
- **Time-series plots** - For date/time columns
- **Distribution histograms** - For numeric data
- **Categorical breakdowns** - For categorical columns

## Code Quality

Built with strict TDD and production standards:

- **476 lines** of implementation (11 modular functions)
- **200+ lines** of tests (16 tests across 4 test files)
- **Full type annotations** throughout
- **80-character line limit** compliance
- **Comprehensive error handling**

## Installation

Requires Python dependencies:

```bash
cd ~/.claude/skills/analysis/quick-descriptive-stats
pip3 install -r requirements.txt
```

Or using uv:
```bash
cd ~/.claude/skills/analysis/quick-descriptive-stats
uv sync
```

## Dependencies

- pandas >= 2.0.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- pytest >= 8.0.0 (dev)
- pytest-cov >= 4.1.0 (dev)

## Documentation

- **[SKILL.md](../../.claude/skills/analysis/quick-descriptive-stats/SKILL.md)** - Official specification
- **[README.md](../../.claude/skills/analysis/quick-descriptive-stats/README.md)** - Installation and usage
- **[examples.md](../../.claude/skills/analysis/quick-descriptive-stats/examples.md)** - Usage examples
- **[reference.md](../../.claude/skills/analysis/quick-descriptive-stats/reference.md)** - Complete API reference

## Command Line Usage

```bash
python ~/.claude/skills/analysis/quick-descriptive-stats/analyze.py data.csv ./output
```

Arguments:
- `data.csv` - Path to CSV file
- `./output` - Output directory for visualizations (optional)

## Testing

Run test suite:
```bash
cd ~/.claude/skills/analysis/quick-descriptive-stats
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

See [README.md](../../.claude/skills/analysis/quick-descriptive-stats/README.md) for complete usage guide and [reference.md](../../.claude/skills/analysis/quick-descriptive-stats/reference.md) for detailed API documentation.
