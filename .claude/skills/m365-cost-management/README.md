# Microsoft 365 Cost Management Skill

Analyze M365 license costs, identify savings opportunities, and generate actionable recommendations.

## Features

- **License Analysis**: Track all M365 SKUs and their costs
- **Inactive User Detection**: Find users with 90+ days no sign-in
- **Utilization Tracking**: Identify unassigned licenses
- **Cost Projections**: Calculate monthly and annual savings potential
- **Interactive Dashboard**: Beautiful HTML dashboard with visualizations
- **CSV Export**: Download user lists for review
- **Recommendations**: Prioritized action items with dollar impact

## Installation

### Prerequisites

- Python 3.10+
- uv package manager
- Microsoft 365 tenant admin access
- Azure AD app registration (for data collection)

### Install Dependencies

```bash
cd ~/.claude/skills/m365-cost-management
uv sync
```

### Azure AD Setup (Required for Data Collection)

1. **Register Azure AD Application**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to Azure Active Directory → App registrations
   - Click "New registration"
   - Name: "M365 Cost Management"
   - Supported account types: "Accounts in this organizational directory only"
   - Click "Register"

2. **Configure API Permissions**:
   - In your app, go to "API permissions"
   - Add permissions:
     - `Organization.Read.All` (Application)
     - `User.Read.All` (Application)
     - `Directory.Read.All` (Application)
   - Click "Grant admin consent"

3. **Create Client Secret**:
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Description: "M365 Cost Tool"
   - Expires: Choose appropriate duration
   - Copy the secret value (you won't see it again)

4. **Configure .env File**:
```bash
# Create .env in skill directory
cat > .env <<EOF
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-app-client-id-here
CLIENT_SECRET=your-client-secret-here
DATABASE_PATH=./data/m365_costs.db
DASHBOARD_OUTPUT=./m365_dashboard.html
INACTIVE_DAYS=90
EOF
```

Find your tenant ID and client ID in the Azure AD app overview page.

## Quick Start

### 1. Collect Data

```bash
uv run python scripts/collect_m365_data.py
```

This will:
- Authenticate to Microsoft Graph API
- Fetch all subscribed SKUs and license assignments
- Collect user sign-in activity in batches (configurable)
- Create checkpoints for resumability
- Handle rate limiting automatically
- Store everything in SQLite database

**For large tenants (1000+ users):**
- Collection runs in batches (default: 100 users per batch)
- Creates checkpoints after each batch
- Can resume if interrupted
- Handles rate limiting with exponential backoff

### 2. Generate Dashboard

```bash
uv run python scripts/generate_dashboard.py
```

Creates `m365_dashboard.html` with:
- Overview: Total costs and savings potential
- Inactive Users: Users with 90+ days no sign-in
- License Utilization: Unassigned licenses
- Actions: Prioritized recommendations
- Warning if data is incomplete

### 3. Review Dashboard

```bash
open m365_dashboard.html
```

Navigate through four tabs:
- **Overview**: Hero metric showing potential cost reduction %
- **Inactive Users**: Download CSV of users to review
- **Utilization**: See which licenses are unused
- **Actions**: Specific next steps with savings impact

## Configuration

All settings use environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `TENANT_ID` | (required) | Azure AD tenant ID |
| `CLIENT_ID` | (required) | App registration client ID |
| `CLIENT_SECRET` | (required) | App client secret |
| `DATABASE_PATH` | `./data/m365_costs.db` | SQLite database location |
| `BATCH_SIZE` | `100` | Users per batch (50-200 recommended) |
| `DASHBOARD_OUTPUT` | `./m365_dashboard.html` | Dashboard output path |
| `INACTIVE_DAYS` | `90` | Days threshold for inactive users |

### Batch Size Guidelines

- **Small tenants (<1K users)**: Use default 100
- **Medium tenants (1-10K users)**: 100-150 for balance
- **Large tenants (10K+ users)**: 150-200 for speed
- **Rate limit issues**: Reduce to 50-75

Smaller batches = more checkpoints, slower but more resilient
Larger batches = fewer checkpoints, faster but less frequent saves

## Incremental Collection & Recovery

### How It Works

The data collection process is designed for resilience with large tenants:

1. **Batch Processing**: Users are processed in batches (default 100)
2. **Checkpoints**: After each batch, progress is saved to database
3. **Rate Limiting**: Automatically detects and handles 429 responses
4. **Progress Tracking**: Real-time status updates throughout collection

### Recovery from Interruptions

If collection is interrupted (Ctrl+C, network issue, rate limit), simply re-run:

```bash
uv run python scripts/collect_m365_data.py
```

The script will:
- Detect the incomplete run
- Resume from the last checkpoint
- Continue where it left off
- Complete the collection

### Monitoring Progress

Check collection status in the database:

```sql
-- View latest collection run
SELECT * FROM collection_runs ORDER BY id DESC LIMIT 1;

-- View progress checkpoints
SELECT * FROM collection_checkpoints
WHERE collection_run_id = (SELECT MAX(id) FROM collection_runs);

-- View retry attempts (rate limiting)
SELECT * FROM retry_log
WHERE collection_run_id = (SELECT MAX(id) FROM collection_runs);
```

### Handling Rate Limits

If you hit rate limits frequently:

1. **Reduce batch size**: Set `BATCH_SIZE=50` in .env
2. **Smaller batches** = more frequent checkpoints + slower API calls
3. **Script logs all retries** for monitoring patterns
4. **Automatic exponential backoff** handles transient limits

## Tools

### collect_m365_data.py

Collects data from Microsoft Graph API.

**Endpoints used**:
- `/subscribedSkus` - License inventory
- `/users?$select=signInActivity` - User activity
- Price lookup from configuration

**Output**: SQLite database with schema:
- `collection_runs` - Run metadata
- `licenses` - License inventory
- `price_lookup` - SKU pricing
- `user_licenses` - User assignments
- `user_activity` - Sign-in dates

### generate_dashboard.py

Creates static HTML dashboard from database.

**Design principles**:
- Jony Ive minimalism
- Edward Tufte data density
- Nord frost color palette
- Self-contained (no external dependencies)

## Database Schema

### collection_runs
- `id` (INTEGER PRIMARY KEY)
- `timestamp` (TEXT)
- `status` (TEXT: 'completed', 'failed')

### licenses
- `collection_run_id` (INTEGER)
- `sku_id` (TEXT)
- `sku_name` (TEXT)
- `total_licenses` (INTEGER)
- `assigned_licenses` (INTEGER)
- `available_licenses` (INTEGER)

### price_lookup
- `sku_id` (TEXT PRIMARY KEY)
- `sku_name` (TEXT)
- `monthly_cost` (REAL)

### user_licenses
- `collection_run_id` (INTEGER)
- `user_principal_name` (TEXT)
- `sku_id` (TEXT)

### user_activity
- `collection_run_id` (INTEGER)
- `user_principal_name` (TEXT PRIMARY KEY)
- `last_sign_in_date` (TEXT)

## Dependencies

| Library | Purpose |
|---------|---------|
| `msal` | Microsoft Authentication Library (Graph API auth) |
| `requests` | HTTP client for Graph API calls |
| `python-dotenv` | Load environment variables from .env |
| `sqlite3` | Database (built-in to Python) |

## Common Tasks

### Monthly License Audit
```bash
# Collect latest data
uv run python tools/collect_m365_data.py

# Generate report
uv run python tools/generate_dashboard.py

# Review unassigned licenses in Utilization tab
open m365_dashboard.html
```

### Quarterly Cost Review
```bash
# Generate dashboard
uv run python tools/generate_dashboard.py

# Open Actions tab for executive summary
open m365_dashboard.html

# Download inactive user CSV for HR review
# (Click download button in Inactive Users tab)
```

### Custom Inactivity Threshold
```bash
# Check 60-day inactive instead of 90
export INACTIVE_DAYS=60
uv run python tools/generate_dashboard.py
```

## Testing

TODO: Test suite to be implemented following TDD practices.

```bash
uv run python -m pytest tests/ -v
```

## Documentation

- **[SKILL.md](SKILL.md)** - Quick reference and usage
- **[examples.md](examples.md)** - Practical workflows
- **[reference.md](reference.md)** - Graph API details and troubleshooting

## Troubleshooting

### Authentication Errors

**Error**: `AADSTS700016: Application not found`
- Verify `CLIENT_ID` matches your Azure AD app
- Check app exists in correct tenant

**Error**: `AADSTS7000215: Invalid client secret`
- Client secret may have expired
- Generate new secret in Azure Portal
- Update `.env` file

### Permission Errors

**Error**: `Insufficient privileges to complete the operation`
- Ensure API permissions are granted
- Click "Grant admin consent" in Azure Portal
- Wait 5-10 minutes for permissions to propagate

### Data Collection Issues

**No data collected**:
- Check Graph API endpoints are accessible
- Verify tenant has active subscriptions
- Review logs for specific error messages

## Cost Savings Checklist

Before removing licenses:
- [ ] Cross-reference with HR termination records
- [ ] Check for extended leave (medical, parental, sabbatical)
- [ ] Exclude service accounts and automation users
- [ ] Obtain IT leadership approval
- [ ] Document all removals for audit trail

## License

Part of Michelle's dotfiles. See [LICENSE](../../../../LICENSE) if applicable.
