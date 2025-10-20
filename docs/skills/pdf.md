# PDF Skill

**Category**: documents
**Location**: `.claude/skills/documents/pdf/`

## Overview

Comprehensive PDF manipulation toolkit providing text extraction, table parsing, document creation, merging/splitting, and form filling capabilities.

## Activation

Activates automatically when working with PDF files or when tasks involve:
- Reading or extracting data from PDFs
- Creating new PDF documents
- Merging or splitting PDF files
- Filling PDF forms
- Converting PDFs to other formats

## Quick Examples

### Extract Text
```python
from scripts.pdf_operations import extract_text

text = extract_text("document.pdf")
page_text = extract_text("document.pdf", page_number=1)
```

### Merge PDFs
```python
from scripts.pdf_operations import merge_pdfs

merge_pdfs(["intro.pdf", "content.pdf"], "combined.pdf")
```

### Extract Tables
```python
import pdfplumber

with pdfplumber.open("report.pdf") as pdf:
    tables = pdf.pages[0].extract_tables()
```

### Fill Forms
```bash
# Check for fillable fields
python scripts/check_fillable_fields.py form.pdf

# Extract field info
python scripts/extract_form_field_info.py form.pdf fields.json

# Fill form
python scripts/fill_fillable_fields.py form.pdf values.json output.pdf
```

## Features

| Feature | Tools |
|---------|-------|
| **Read & Extract** | pypdf, pdfplumber |
| **Text Extraction** | Extract from all pages or specific pages |
| **Table Extraction** | Parse tables into pandas DataFrames |
| **Metadata** | Extract title, author, page count |
| **Create PDFs** | reportlab for generation from scratch |
| **Merge/Split** | Combine multiple PDFs or split into pages |
| **Form Filling** | Both fillable and non-fillable forms |
| **Convert** | PDF to images for analysis |

## Dependencies

- **pypdf** - Core PDF reading/writing
- **pdfplumber** - Text and table extraction
- **reportlab** - PDF creation
- **pdf2image** - Convert to images
- **poppler-utils** - System backend

## Installation

```bash
cd ~/.claude/skills/documents/pdf
uv sync
```

System dependencies:
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils
```

## Use Cases

### Document Processing
- Extract text from scanned documents
- Parse financial reports and extract tables
- Combine multiple documents into one

### Form Automation
- Auto-fill application forms
- Batch process forms with different data
- Validate form fields before submission

### Document Analysis
- Extract metadata for cataloging
- Convert to images for visual analysis
- Parse structured data from PDFs

## Documentation

- **[SKILL.md](../../.claude/skills/documents/pdf/SKILL.md)** - Quick reference
- **[examples.md](../../.claude/skills/documents/pdf/examples.md)** - Usage examples
- **[forms.md](../../.claude/skills/documents/pdf/forms.md)** - Form filling workflow
- **[reference.md](../../.claude/skills/documents/pdf/reference.md)** - Advanced features
- **[README.md](../../.claude/skills/documents/pdf/README.md)** - Setup guide

## Error Handling

All operations use `PDFOperationError` exception:

```python
from scripts.pdf_operations import PDFOperationError

try:
    # PDF operations
except PDFOperationError as e:
    print(f"PDF operation failed: {e}")
```

Common errors handled:
- File not found
- Corrupted PDFs
- Invalid page numbers
- Empty merge lists
- Invalid output paths
- Permission errors

## Testing

Comprehensive test suite with TDD approach:

```bash
cd ~/.claude/skills/documents/pdf
uv run python -m pytest tests/ -v
```

Tests cover:
- Basic read/write operations
- Text and metadata extraction
- Merging and splitting
- Form field detection
- Error handling
- Edge cases

## See Also

- [Test-Driven Development](test-driven-development.md) - TDD workflow
- [Quick Descriptive Stats](quick-descriptive-stats.md) - For CSV data from PDFs
