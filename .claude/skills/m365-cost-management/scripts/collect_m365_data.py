#!/usr/bin/env python3
"""
Collect M365 license and usage data via Microsoft Graph API.

Authenticates using MSAL (Microsoft Authentication Library) with
client credentials flow, fetches license data, user activity, and
license assignments from Graph API, then stores everything in SQLite.

Requires .env file with:
    TENANT_ID=your-tenant-id
    CLIENT_ID=your-app-client-id
    CLIENT_SECRET=your-app-secret
    DATABASE_PATH=./data/m365_costs.db (optional)
"""

import os
import sqlite3
import sys
from datetime import datetime
from typing import Any

import requests
from dotenv import load_dotenv
from msal import ConfidentialClientApplication


def create_database_schema(db_path: str) -> None:
    """
    Create database schema for M365 cost data.

    Args:
        db_path: Path to SQLite database file
    """
    # Ensure parent directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Collection runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collection_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            status TEXT NOT NULL CHECK(status IN ('completed', 'failed', 'running')),
            error_message TEXT,
            records_collected INTEGER
        )
    """)

    # Licenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_run_id INTEGER NOT NULL,
            sku_id TEXT NOT NULL,
            sku_name TEXT NOT NULL,
            total_licenses INTEGER NOT NULL,
            assigned_licenses INTEGER NOT NULL,
            available_licenses INTEGER NOT NULL,
            FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id)
        )
    """)

    # Price lookup table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_lookup (
            sku_id TEXT PRIMARY KEY,
            sku_name TEXT NOT NULL,
            monthly_cost REAL NOT NULL CHECK(monthly_cost >= 0),
            last_updated TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # User licenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_run_id INTEGER NOT NULL,
            user_principal_name TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id),
            UNIQUE(collection_run_id, user_principal_name, sku_id)
        )
    """)

    # User activity table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_run_id INTEGER NOT NULL,
            user_principal_name TEXT NOT NULL,
            last_sign_in_date TEXT,
            FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id),
            UNIQUE(collection_run_id, user_principal_name)
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_licenses_run
        ON licenses(collection_run_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_licenses_run
        ON user_licenses(collection_run_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_activity_run
        ON user_activity(collection_run_id)
    """)

    conn.commit()
    conn.close()


def start_collection_run(db_path: str) -> int:
    """
    Start a new collection run.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Run ID for this collection
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO collection_runs (status)
        VALUES ('running')
    """)

    run_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return run_id


def complete_collection_run(
    db_path: str,
    run_id: int,
    success: bool,
    records: int | None = None,
    error_message: str | None = None
) -> None:
    """
    Mark collection run as completed or failed.

    Args:
        db_path: Path to SQLite database file
        run_id: Collection run ID
        success: Whether collection succeeded
        records: Number of records collected (if successful)
        error_message: Error message (if failed)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    status = 'completed' if success else 'failed'

    cursor.execute("""
        UPDATE collection_runs
        SET status = ?,
            error_message = ?,
            records_collected = ?
        WHERE id = ?
    """, (status, error_message, records, run_id))

    conn.commit()
    conn.close()


def store_licenses(
    db_path: str,
    run_id: int,
    skus: list[dict[str, Any]]
) -> None:
    """
    Store license data from Graph API subscribedSkus response.

    Args:
        db_path: Path to SQLite database file
        run_id: Collection run ID
        skus: List of SKU objects from Graph API
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for sku in skus:
        sku_id = sku['skuId']
        sku_name = sku['skuPartNumber']
        total = sku['prepaidUnits']['enabled']
        assigned = sku['consumedUnits']
        available = total - assigned

        cursor.execute("""
            INSERT INTO licenses (
                collection_run_id,
                sku_id,
                sku_name,
                total_licenses,
                assigned_licenses,
                available_licenses
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (run_id, sku_id, sku_name, total, assigned, available))

    conn.commit()
    conn.close()


def store_user_activity(
    db_path: str,
    run_id: int,
    users: list[dict[str, Any]]
) -> None:
    """
    Store user sign-in activity from Graph API users response.

    Args:
        db_path: Path to SQLite database file
        run_id: Collection run ID
        users: List of user objects with signInActivity from Graph API
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for user in users:
        upn = user['userPrincipalName']
        sign_in = user.get('signInActivity')
        last_sign_in = None

        if sign_in:
            last_sign_in = sign_in.get('lastSignInDateTime')

        cursor.execute("""
            INSERT OR REPLACE INTO user_activity (
                collection_run_id,
                user_principal_name,
                last_sign_in_date
            ) VALUES (?, ?, ?)
        """, (run_id, upn, last_sign_in))

    conn.commit()
    conn.close()


def store_user_licenses(
    db_path: str,
    run_id: int,
    user_licenses: dict[str, dict[str, list[dict[str, Any]]]]
) -> None:
    """
    Store user license assignments.

    Args:
        db_path: Path to SQLite database file
        run_id: Collection run ID
        user_licenses: Dict mapping UPN to license details response
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for upn, license_data in user_licenses.items():
        for license in license_data.get('value', []):
            sku_id = license['skuId']

            cursor.execute("""
                INSERT OR IGNORE INTO user_licenses (
                    collection_run_id,
                    user_principal_name,
                    sku_id
                ) VALUES (?, ?, ?)
            """, (run_id, upn, sku_id))

    conn.commit()
    conn.close()


def initialize_default_prices(db_path: str) -> None:
    """
    Initialize price lookup table with default Microsoft 365 pricing.

    Prices are approximate and should be updated based on your
    actual enterprise agreement pricing.

    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    default_prices = [
        # Office 365 Plans
        ('c7df2760-2c81-4ef7-b578-5b5392b571df', 'ENTERPRISEPREMIUM', 38.00),
        ('18181a46-0d4e-45cd-891e-60aabd171b4e', 'ENTERPRISEPACK', 23.00),
        ('6fd2c87f-b296-42f0-b197-1e91e994b900', 'STANDARDPACK', 12.50),

        # Microsoft 365 Plans
        ('26d45bd9-adf1-46cd-a9e1-51e9a5524128', 'Microsoft 365 E3', 36.00),
        ('06ebc4ee-1bb5-47dd-8120-11324bc54e06', 'Microsoft 365 E5', 57.00),
        ('3b555118-da6a-4418-894f-7df1e2096870', 'Microsoft 365 Business Basic', 6.00),
        ('f245ecc8-75af-4f8e-b61f-27d8114de5f3', 'Microsoft 365 Business Standard', 12.50),
        ('cbdc14ab-d96c-4c30-b9f4-6ada7cdc1d46', 'Microsoft 365 Business Premium', 22.00),

        # Add-ons
        ('f30db892-07e9-47e9-837c-80727f46fd3d', 'Microsoft Flow Free', 0.00),
        ('26d45bd9-adf1-46cd-a9e1-51e9a5524128', 'Power BI Pro', 9.99),
        ('a403ebcc-fae0-4ca2-8c8c-7a907fd6c235', 'Power BI Premium', 20.00),
        ('440eaaa8-b3e0-484b-a8be-62870b9ba70a', 'Visio Plan 2', 15.00),
        ('4b590615-0888-425a-a965-b3bf7789848d', 'Project Plan 3', 30.00),
    ]

    for sku_id, sku_name, monthly_cost in default_prices:
        cursor.execute("""
            INSERT OR REPLACE INTO price_lookup (
                sku_id,
                sku_name,
                monthly_cost,
                last_updated
            ) VALUES (?, ?, ?, datetime('now'))
        """, (sku_id, sku_name, monthly_cost))

    conn.commit()
    conn.close()


def authenticate_graph_api(
    tenant_id: str,
    client_id: str,
    client_secret: str
) -> str:
    """
    Authenticate to Microsoft Graph API using client credentials.

    Args:
        tenant_id: Azure AD tenant ID
        client_id: Application (client) ID
        client_secret: Client secret value

    Returns:
        Access token for Graph API

    Raises:
        Exception: If authentication fails
    """
    app = ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret
    )

    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )

    if "access_token" in result:
        return result["access_token"]
    else:
        error = result.get("error", "Unknown error")
        error_desc = result.get("error_description", "No description")
        raise Exception(f"Authentication failed: {error} - {error_desc}")


def fetch_subscribed_skus(access_token: str) -> list[dict[str, Any]]:
    """
    Fetch all subscribed SKUs from Graph API.

    Args:
        access_token: Graph API access token

    Returns:
        List of SKU objects
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(
        'https://graph.microsoft.com/v1.0/subscribedSkus',
        headers=headers
    )
    response.raise_for_status()

    return response.json()['value']


def fetch_users_with_activity(access_token: str) -> list[dict[str, Any]]:
    """
    Fetch all users with sign-in activity from Graph API.

    Handles pagination to retrieve all users.

    Args:
        access_token: Graph API access token

    Returns:
        List of user objects with signInActivity
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    all_users = []
    url = 'https://graph.microsoft.com/v1.0/users'
    params = {
        '$select': 'userPrincipalName,signInActivity',
        '$top': 999
    }

    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        all_users.extend(data['value'])

        # Get next page URL
        url = data.get('@odata.nextLink')
        params = None  # nextLink includes all params

    return all_users


def fetch_user_licenses(
    access_token: str,
    users: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """
    Fetch license details for each user.

    Args:
        access_token: Graph API access token
        users: List of user objects

    Returns:
        Dict mapping UPN to license details response
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    user_licenses = {}

    for user in users:
        upn = user['userPrincipalName']

        response = requests.get(
            f'https://graph.microsoft.com/v1.0/users/{upn}/licenseDetails',
            headers=headers
        )

        if response.status_code == 200:
            user_licenses[upn] = response.json()
        elif response.status_code == 404:
            # User not found or not accessible
            print(f"Warning: Could not fetch licenses for {upn}")
            user_licenses[upn] = {'value': []}
        else:
            response.raise_for_status()

    return user_licenses


def main() -> int:
    """
    Main function to collect M365 data and store in database.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Load environment variables
    load_dotenv()

    tenant_id = os.getenv('TENANT_ID')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    db_path = os.getenv('DATABASE_PATH', './data/m365_costs.db')

    # Validate configuration
    if not all([tenant_id, client_id, client_secret]):
        print("Error: Missing required environment variables")
        print("Required: TENANT_ID, CLIENT_ID, CLIENT_SECRET")
        print("Create a .env file with these values")
        return 1

    try:
        # Setup database
        print("Setting up database...")
        create_database_schema(db_path)
        initialize_default_prices(db_path)

        # Start collection run
        run_id = start_collection_run(db_path)
        print(f"Started collection run {run_id}")

        # Authenticate
        print("Authenticating to Microsoft Graph API...")
        access_token = authenticate_graph_api(
            tenant_id,
            client_id,
            client_secret
        )
        print("Authentication successful")

        # Fetch license data
        print("Fetching subscribed SKUs...")
        skus = fetch_subscribed_skus(access_token)
        print(f"Found {len(skus)} SKUs")
        store_licenses(db_path, run_id, skus)

        # Fetch user activity
        print("Fetching users with sign-in activity...")
        users = fetch_users_with_activity(access_token)
        print(f"Found {len(users)} users")
        store_user_activity(db_path, run_id, users)

        # Fetch user licenses
        print("Fetching user license assignments...")
        user_licenses = fetch_user_licenses(access_token, users)
        total_assignments = sum(
            len(lic['value']) for lic in user_licenses.values()
        )
        print(f"Found {total_assignments} license assignments")
        store_user_licenses(db_path, run_id, user_licenses)

        # Complete run
        total_records = len(skus) + len(users) + len(user_licenses)
        complete_collection_run(db_path, run_id, success=True, records=total_records)

        print(f"\nCollection complete!")
        print(f"Total records: {total_records}")
        print(f"Database: {db_path}")
        print(f"\nNext step: Generate dashboard with generate_dashboard.py")

        return 0

    except Exception as e:
        print(f"\nError during collection: {e}")

        # Mark run as failed if we have a run_id
        if 'run_id' in locals():
            complete_collection_run(
                db_path,
                run_id,
                success=False,
                error_message=str(e)
            )

        return 1


if __name__ == '__main__':
    sys.exit(main())
