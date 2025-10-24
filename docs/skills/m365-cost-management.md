# M365 Cost Management Skill

**Category**: cost analysis
**Location**: `.claude/skills/m365-cost-management/`

## Overview

Comprehensive toolkit for analyzing Microsoft 365 license costs, identifying inactive users, tracking utilization, and generating actionable cost reduction recommendations.

## Activation

Activates automatically when tasks involve:
- Preparing quarterly cost reviews
- Responding to budget reduction requests
- Auditing license compliance
- Analyzing SaaS spending
- Onboarding/offboarding users at scale
- Optimizing M365 costs

## Quick Examples

### Collect M365 Data
```bash
cd ~/.claude/skills/m365-cost-management
uv run python scripts/collect_m365_data.py
```

### Generate Dashboard
```bash
uv run python scripts/generate_dashboard.py
open m365_dashboard.html
```

## Features

| Feature | What It Does |
|---------|--------------|
| **Inactive Users** | Identify users with 90+ days no sign-in |
| **Unassigned Licenses** | Find purchased but unallocated licenses |
| **Cost Analysis** | Calculate monthly/annual costs by license type |
| **Utilization Tracking** | Track license assignment percentages |
| **Interactive Dashboard** | Chart.js visualizations with Nord frost theme |
| **Actionable Recommendations** | Prioritized list sorted by savings impact |

## What This Identifies

### Cost Savings Through
- Inactive users (90+ days without sign-in)
- Unassigned licenses (purchased but not allocated)
- Underutilized license types

### Insights Provided
- Total monthly/annual costs by license type
- Utilization percentages
- Potential cost reduction percentage
- Prioritized action items

### Deliverables
- Interactive HTML dashboard (Chart.js visualizations)
- Downloadable CSV of inactive users
- Specific recommendations with cost impact

## Dashboard Views

**Overview:**
- Hero metric: potential cost reduction percentage
- Top 8 license costs (horizontal bar chart)
- Total monthly spend

**Inactive Users:**
- Count of users with 90+ days no sign-in
- Cost impact by license type
- Downloadable user list

**License Utilization:**
- Unassigned licenses by type
- Monthly waste calculation
- Detail table with per-license costs

**Actions:**
- Prioritized recommendations sorted by savings
- Pre-flight checklist (verify with HR, check leave status)
- Ongoing process guidelines

## Installation

```bash
cd ~/.claude/skills/m365-cost-management
uv sync
```

## Dependencies

Required Python packages:
- **msal** - Microsoft Authentication Library
- **requests** - HTTP client for Graph API
- **python-dotenv** - Environment variable management
- **sqlite3** - Database (built-in)

## Configuration

Create `.env` file with M365 credentials:
```bash
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
```

Requires:
- M365 tenant admin credentials
- Azure AD app registration with appropriate permissions

## Database Schema

SQLite database with tables:
- `collection_runs` - Metadata for each data collection
- `licenses` - License inventory and assignments
- `price_lookup` - Cost per SKU
- `user_licenses` - User-to-license mappings
- `user_activity` - Last sign-in dates

## Use Cases

### Quarterly Reviews
- Generate dashboard before finance meetings
- Identify cost reduction opportunities
- Track utilization trends over time

### Budget Reduction
- Respond quickly to cost cutting requests
- Quantify savings from removing inactive users
- Prioritize actions by impact

### License Compliance
- Audit license assignments
- Identify over-provisioning
- Track license inventory

### User Lifecycle Management
- Automate inactive user detection
- Streamline offboarding workflows
- Optimize license allocation

## Critical Workflow

1. **Configure**: Set up Azure AD app and `.env` file
2. **Collect**: Run `collect_m365_data.py` to gather data
3. **Generate**: Create dashboard with `generate_dashboard.py`
4. **Review**: Open HTML dashboard in browser
5. **Act**: Export inactive users CSV and implement recommendations
6. **Verify**: Confirm with HR before removing licenses
7. **Repeat**: Run monthly or quarterly

## Design Principles

- **Nord Frost Color Scheme**: Jony Ive / Tufte-inspired minimalism
- **Embedded Data**: No external dependencies for dashboard
- **Actionable**: Every insight includes specific next step
- **Verifiable**: Export lists for HR/manager confirmation
- **Safe**: Pre-flight checklist prevents accidental removals

## Documentation

- **[SKILL.md](../../.claude/skills/m365-cost-management/SKILL.md)** - Quick reference
- **[examples.md](../../.claude/skills/m365-cost-management/examples.md)** - Usage examples
- **[reference.md](../../.claude/skills/m365-cost-management/reference.md)** - Graph API details
- **[README.md](../../.claude/skills/m365-cost-management/README.md)** - Setup guide

## See Also

- [Quick Descriptive Stats](quick-descriptive-stats.md) - For data analysis
- [Excel/XLSX](xlsx.md) - For spreadsheet reporting
- [Test-Driven Development](test-driven-development.md) - TDD workflow
