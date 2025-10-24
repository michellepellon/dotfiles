---
name: m365-cost-management
description: Analyze Microsoft 365 license costs, identify inactive users, track license utilization, and generate actionable cost reduction recommendations. Use when optimizing SaaS spending, auditing license compliance, or preparing cost reduction initiatives.
when_to_use: When preparing quarterly cost reviews. When responding to budget reduction requests. When auditing license compliance. When analyzing SaaS spending. When onboarding/offboarding users at scale.
allowed-tools: Read, Write, Bash
---

# Microsoft 365 Cost Management

Comprehensive toolkit for analyzing M365 license costs and identifying savings opportunities.

**Announce at start:** "I'm using the m365-cost-management skill to analyze license costs."

## Quick Start

1. **Collect data** from M365 tenant:
   ```bash
   uv run python scripts/collect_m365_data.py
   ```

2. **Generate dashboard**:
   ```bash
   uv run python scripts/generate_dashboard.py
   ```

3. **Open dashboard** in browser:
   ```bash
   open m365_dashboard.html
   ```

## What This Does

**Identifies savings** through:
- Inactive users (90+ days without sign-in)
- Unassigned licenses (purchased but not allocated)
- Underutilized license types

**Generates insights**:
- Total monthly/annual costs by license type
- Utilization percentages
- Potential cost reduction percentage
- Prioritized action items

**Produces deliverables**:
- Interactive HTML dashboard (Chart.js visualizations)
- Downloadable CSV of inactive users
- Specific recommendations with cost impact

## When to Use

**Use this skill when:**
- Preparing quarterly cost reviews
- Responding to budget reduction requests
- Auditing license compliance
- Onboarding/offboarding users at scale
- Optimizing SaaS spending

**Don't use when:**
- Current codebase questions (use Grep/Read)
- Other SaaS platforms (Azure, AWS, etc.)

## Tools

### collect_m365_data.py (TODO)
Connects to Microsoft Graph API to collect:
- License inventory (SKUs, quantities, assignments)
- User activity (last sign-in dates)
- Price lookup data

**Requirements:**
- M365 tenant admin credentials
- Azure AD app registration with appropriate permissions
- `.env` file with authentication details

### generate_dashboard.py
Creates static HTML dashboard from collected data.

**Features:**
- Nord frost color scheme (Jony Ive / Tufte design principles)
- Four views: Overview, Inactive Users, Utilization, Actions
- Embedded data (no external dependencies)
- Export inactive users to CSV

**Configuration:**
```bash
DATABASE_PATH=./data/m365_costs.db
DASHBOARD_OUTPUT=./m365_dashboard.html
```

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

## Database Schema

SQLite database with tables:
- `collection_runs` - Metadata for each data collection
- `licenses` - License inventory and assignments
- `price_lookup` - Cost per SKU
- `user_licenses` - User-to-license mappings
- `user_activity` - Last sign-in dates

## Dependencies

Required Python packages:
- `msal` - Microsoft Authentication Library
- `requests` - HTTP client for Graph API
- `python-dotenv` - Environment variable management
- `sqlite3` - Database (built-in)

## See Also

- `examples.md` - Common workflows and use cases
- `README.md` - Installation and setup
- `reference.md` - Graph API details and troubleshooting
