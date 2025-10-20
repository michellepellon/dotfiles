# Excel/XLSX Skill

**Category**: documents
**Location**: `.claude/skills/documents/xlsx/`

## Overview

Comprehensive Excel spreadsheet toolkit providing data analysis, formula creation, formatting per financial model standards, and automated formula recalculation.

## Activation

Activates automatically when working with Excel files or when tasks involve:
- Reading or analyzing spreadsheet data
- Creating financial models
- Working with formulas and calculations
- Applying financial model formatting standards
- Data reporting and visualization

## Quick Examples

### Read Excel Data
```python
from scripts.xlsx_operations import read_excel

df = read_excel('sales.xlsx')
print(df.describe())
```

### Create with Formulas
```python
from openpyxl import Workbook
from scripts.xlsx_operations import add_formula, set_cell_color

wb = Workbook()
ws = wb.active

ws['A1'] = 'Revenue'
ws['B1'] = 100000
set_cell_color(ws, 'B1', 'blue')  # Input

add_formula(ws, 'B2', '=B1*1.1')
set_cell_color(ws, 'B2', 'black')  # Formula

wb.save('model.xlsx')
```

### Recalculate Formulas
```bash
python scripts/recalc.py model.xlsx
```

## Features

| Feature | Tools |
|---------|-------|
| **Read & Analyze** | pandas for data analysis |
| **Create & Edit** | openpyxl for Excel operations |
| **Formulas** | Add Excel formulas, not hardcoded values |
| **Color Coding** | Financial model standards (blue/black/green/red) |
| **Recalculation** | LibreOffice integration for formula verification |
| **Error Detection** | Scan for #REF!, #DIV/0!, #VALUE!, etc. |

## Financial Model Standards

### Color Coding

| Color | Use Case | RGB |
|-------|----------|-----|
| Blue | Hardcoded inputs | 0,0,255 |
| Black | Formulas | 0,0,0 |
| Green | Internal links | 0,128,0 |
| Red | External links | 255,0,0 |
| Yellow bg | Key assumptions | 255,255,0 |

### Number Formatting

- Years as text ("2024" not "2,024")
- Currency: $#,##0 format
- Zeros display as "-"
- Percentages: 0.0%
- Negatives: (123) not -123

## Dependencies

- **pandas** - Data analysis and I/O
- **openpyxl** - Excel file manipulation
- **LibreOffice** - Formula recalculation

## Installation

```bash
cd ~/.claude/skills/documents/xlsx
uv sync

# Install LibreOffice
brew install libreoffice  # macOS
sudo apt-get install libreoffice  # Ubuntu/Debian
```

## Use Cases

### Data Analysis
- Read Excel files into pandas DataFrames
- Perform statistical analysis
- Create pivot tables and summaries
- Export results to Excel

### Financial Modeling
- Build revenue projections
- Create income statements
- Develop scenario analyses
- Apply standard formatting

### Reporting
- Generate formatted reports
- Combine data from multiple sources
- Add formulas for dynamic updates
- Ensure zero formula errors

## Critical Workflow

1. **Create/Edit**: Build Excel file with formulas
2. **Recalculate**: `python scripts/recalc.py file.xlsx`
3. **Verify**: Check JSON output for errors
4. **Fix**: Correct any formula errors
5. **Repeat**: Recalculate until zero errors

**Never deliver Excel files with formula errors.**

## Documentation

- **[SKILL.md](../../.claude/skills/documents/xlsx/SKILL.md)** - Quick reference
- **[examples.md](../../.claude/skills/documents/xlsx/examples.md)** - Usage examples
- **[README.md](../../.claude/skills/documents/xlsx/README.md)** - Setup guide

## Error Handling

All operations use `ExcelOperationError` exception:

```python
from scripts.xlsx_operations import ExcelOperationError

try:
    df = read_excel('data.xlsx')
except ExcelOperationError as e:
    print(f"Failed: {e}")
```

Formula recalculation detects:
- #REF! - Invalid references
- #DIV/0! - Division by zero
- #VALUE! - Wrong data type
- #NAME? - Unrecognized name
- #NULL! - Null intersection
- #NUM! - Invalid number
- #N/A - Value not available

## Testing

Comprehensive TDD test suite:

```bash
cd ~/.claude/skills/documents/xlsx
uv run python -m pytest tests/ -v
```

Tests cover:
- Basic read/write operations
- Formula creation and verification
- Color coding standards
- pandas integration
- Error handling
- Multi-sheet workbooks

## See Also

- [PDF](pdf.md) - For PDF documents
- [Quick Descriptive Stats](quick-descriptive-stats.md) - For CSV analysis
- [Test-Driven Development](test-driven-development.md) - TDD workflow
