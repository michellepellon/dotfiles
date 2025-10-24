#!/usr/bin/env python3
"""
Update price_lookup table with correct SKU IDs and comprehensive pricing.

This script syncs the price_lookup table with actual SKUs found in the
licenses table and sets appropriate monthly costs based on Microsoft's
published pricing.
"""

import os
import sqlite3
import sys
from dotenv import load_dotenv


# Microsoft 365 SKU pricing (as of 2024, monthly per user)
# Source: Microsoft 365 pricing pages
SKU_PRICING = {
    # Enterprise plans
    'ENTERPRISEPREMIUM': ('Microsoft 365 E5', 57.00),
    'ENTERPRISEPACK': ('Microsoft 365 E3', 36.00),
    'STANDARDPACK': ('Office 365 E1', 8.00),
    'STANDARDWOFFPACK': ('Office 365 E2', 10.00),
    'DESKLESSPACK': ('Microsoft 365 F3', 8.00),

    # Business plans
    'O365_BUSINESS_ESSENTIALS': ('Microsoft 365 Business Basic', 6.00),
    'O365_BUSINESS_PREMIUM': ('Microsoft 365 Business Premium', 22.00),
    'O365_BUSINESS': ('Microsoft 365 Apps for business', 8.25),
    'SPB': ('Microsoft 365 Business Premium', 22.00),
    'SMB_BUSINESS': ('Microsoft 365 Business Basic', 6.00),
    'SMB_BUSINESS_PREMIUM': ('Microsoft 365 Business Premium', 22.00),

    # E3/E5 variants
    'Microsoft_365_E3_(no_Teams)': ('Microsoft 365 E3 (no Teams)', 36.00),
    'SPE_E3': ('Microsoft 365 E3', 36.00),
    'SPE_E5': ('Microsoft 365 E5', 57.00),

    # Exchange
    'EXCHANGESTANDARD': ('Exchange Online Plan 1', 4.00),
    'EXCHANGEENTERPRISE': ('Exchange Online Plan 2', 8.00),
    'EXCHANGEDESKLESS': ('Exchange Online Kiosk', 2.00),

    # SharePoint
    'SHAREPOINTSTANDARD': ('SharePoint Online Plan 1', 5.00),
    'SHAREPOINTENTERPRISE': ('SharePoint Online Plan 2', 10.00),
    'SHAREPOINTSTORAGE': ('SharePoint Online Storage', 0.20),  # per GB

    # Teams & Communication
    'MCOSTANDARD': ('Microsoft Teams Essentials', 4.00),
    'MCOPSTN1': ('Calling Plan', 12.00),
    'MCOPSTNC': ('Communication Credits', 0.00),  # Variable
    'PHONESYSTEM_VIRTUALUSER': ('Phone System Virtual User', 15.00),
    'Microsoft_Teams_Rooms_Basic': ('Teams Rooms Basic', 0.00),  # Free
    'Microsoft_Teams_Rooms_Pro': ('Teams Rooms Pro', 40.00),

    # Power Platform
    'FLOW_FREE': ('Power Automate Free', 0.00),
    'FLOW_PER_USER': ('Power Automate per user', 15.00),
    'POWERAUTOMATE_ATTENDED_RPA': ('Power Automate attended RPA', 40.00),
    'POWERAPPS_PER_USER': ('Power Apps per user', 20.00),
    'POWERAPPS_PER_APP_NEW': ('Power Apps per app', 5.00),
    'POWERAPPS_DEV': ('Power Apps Developer', 0.00),  # Free
    'POWER_BI_PRO': ('Power BI Pro', 9.99),
    'POWER_BI_STANDARD': ('Power BI Premium', 20.00),

    # Project & Visio
    'PROJECTPROFESSIONAL': ('Project Plan 5', 55.00),
    'PROJECT_P1': ('Project Plan 1', 10.00),
    'PROJECTESSENTIALS': ('Project Plan 3', 30.00),
    'VISIOCLIENT': ('Visio Plan 2', 15.00),
    'VISIO_PLAN1': ('Visio Plan 1', 5.00),

    # Dynamics 365
    'DYN365_BUSCENTRAL_ESSENTIAL': ('Dynamics 365 Business Central Essentials', 70.00),
    'DYN365_BUSCENTRAL_TEAM_MEMBER': ('Dynamics 365 Business Central Team Member', 8.00),
    'DYN365_FINANCIALS_ACCOUNTANT_SKU': ('Dynamics 365 Business Central Accountant', 0.00),  # Free
    'D365_MARKETING_USER': ('Dynamics 365 Marketing', 1500.00),  # Per tenant

    # Security & Compliance
    'AAD_PREMIUM': ('Azure AD Premium P1', 6.00),
    'AAD_PREMIUM_P2': ('Azure AD Premium P2', 9.00),
    'INTUNE_A': ('Microsoft Intune', 6.00),
    'INTUNE_A_D': ('Microsoft Intune Device', 6.00),
    'INTUNE_DEVICE_ENTERPRISE_New': ('Microsoft Intune Device', 6.00),
    'EMS': ('Enterprise Mobility + Security E3', 10.60),

    # Microsoft 365 Copilot
    'Microsoft_365_Copilot': ('Microsoft 365 Copilot', 30.00),

    # Forms & Stream
    'FORMS_PRO': ('Microsoft Forms Pro', 200.00),  # Per tenant
    'STREAM': ('Microsoft Stream', 0.00),  # Included

    # Other/Legacy
    'WINDOWS_STORE': ('Windows Store for Business', 0.00),
    'SPZA_IW': ('App Connect', 0.00),
    'CPC_B_2C_4RAM_64GB_WHB': ('Cloud PC', 31.00),
    'CCIBOTS_PRIVPREV_VIRAL': ('Copilot Studio Trial', 0.00),
    'PROJECT_MADEIRA_PREVIEW_IW_SKU': ('Business Central Preview', 0.00),
}


def update_price_lookup(db_path: str):
    """
    Update price_lookup table to match actual SKUs from licenses table.

    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all unique SKUs from licenses table
    cursor.execute("""
        SELECT DISTINCT sku_id, sku_name
        FROM licenses
        ORDER BY sku_name
    """)
    actual_skus = cursor.fetchall()

    print(f"Found {len(actual_skus)} unique SKUs in licenses table")

    # Clear existing price_lookup table
    cursor.execute("DELETE FROM price_lookup")

    # Insert prices for each SKU
    inserted = 0
    missing = []

    for sku_id, sku_name in actual_skus:
        if sku_name in SKU_PRICING:
            friendly_name, monthly_cost = SKU_PRICING[sku_name]
            cursor.execute("""
                INSERT INTO price_lookup (sku_id, sku_name, monthly_cost)
                VALUES (?, ?, ?)
            """, (sku_id, sku_name, monthly_cost))
            inserted += 1
            print(f"  ✓ {sku_name}: ${monthly_cost}/mo ({friendly_name})")
        else:
            # Insert with $0 cost for unknown SKUs
            cursor.execute("""
                INSERT INTO price_lookup (sku_id, sku_name, monthly_cost)
                VALUES (?, ?, ?)
            """, (sku_id, sku_name, 0.00))
            missing.append(sku_name)
            print(f"  ? {sku_name}: $0.00/mo (UNKNOWN - please set manually)")

    conn.commit()
    conn.close()

    print(f"\nUpdated {inserted} SKUs with pricing")

    if missing:
        print(f"\nWarning: {len(missing)} SKUs have no pricing data:")
        for sku in missing:
            print(f"  - {sku}")
        print("\nPlease set prices manually for these SKUs using the dashboard Pricing tab.")

    print("\nPrice lookup table updated successfully!")


def main():
    load_dotenv()

    db_path = os.getenv('DATABASE_PATH', './data/m365_costs.db')

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Run collect_m365_data.py first to collect data.")
        sys.exit(1)

    print(f"Updating price_lookup table in {db_path}...")
    print()

    update_price_lookup(db_path)


if __name__ == '__main__':
    main()
