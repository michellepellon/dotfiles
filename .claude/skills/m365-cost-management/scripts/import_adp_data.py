#!/usr/bin/env python3
"""
Import ADP employee data and cross-reference with M365 licenses.

This script imports ADP HR export data and provides analysis functions
to identify:
- M365 users not in ADP (orphaned licenses)
- ADP terminated employees with active M365 licenses
- Active employees with no M365 activity
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta

import openpyxl
from dotenv import load_dotenv


def parse_adp_excel(file_path: str) -> list[dict]:
    """
    Parse ADP Excel export file.

    Args:
        file_path: Path to ADP Excel export

    Returns:
        List of employee dictionaries
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ADP file not found: {file_path}")

    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    # Get headers from first row
    headers = [cell.value for cell in sheet[1]]

    # Map expected column names to indices
    column_map = {
        'legal_name': 'Legal Name',
        'preferred_first_name': 'Preferred or Chosen First Name',
        'preferred_last_name': 'Preferred or Chosen Last Name',
        'position_id': 'Position ID',
        'hire_date': 'Hire Date',
        'job_title': 'Job Title Description',
        'position_start_date': 'Position Start Date',
        'position_status': 'Position Status',
        'location': 'Location Description',
        'work_email': 'Work Contact: Work Email',
    }

    # Find column indices
    col_indices = {}
    for key, col_name in column_map.items():
        try:
            col_indices[key] = headers.index(col_name)
        except ValueError:
            print(f"Warning: Column '{col_name}' not found in ADP export")
            col_indices[key] = None

    # Parse all rows
    employees = []
    for row_num in range(2, sheet.max_row + 1):
        row = [cell.value for cell in sheet[row_num]]

        # Skip rows without email (required field)
        if col_indices['work_email'] is None:
            continue

        email = row[col_indices['work_email']]
        if not email:
            continue

        employee = {}
        for key, idx in col_indices.items():
            if idx is not None:
                value = row[idx]
                # Convert datetime objects to ISO format strings
                if isinstance(value, datetime):
                    value = value.date().isoformat()
                employee[key] = value
            else:
                employee[key] = None

        employees.append(employee)

    return employees


def import_adp_data(file_path: str, db_path: str) -> dict:
    """
    Import ADP data into database.

    Args:
        file_path: Path to ADP Excel export
        db_path: Path to SQLite database

    Returns:
        Dictionary with import results
    """
    employees = parse_adp_excel(file_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create ADP table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adp_employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_timestamp TEXT NOT NULL,
            legal_name TEXT,
            preferred_first_name TEXT,
            preferred_last_name TEXT,
            position_id TEXT,
            hire_date TEXT,
            job_title TEXT,
            position_start_date TEXT,
            position_status TEXT,
            location TEXT,
            work_email TEXT NOT NULL
        )
    """)

    # Clear existing data
    cursor.execute("DELETE FROM adp_employees")

    # Insert new data
    timestamp = datetime.now().isoformat()
    inserted = 0

    for emp in employees:
        cursor.execute("""
            INSERT INTO adp_employees (
                import_timestamp, legal_name, preferred_first_name,
                preferred_last_name, position_id, hire_date, job_title,
                position_start_date, position_status, location, work_email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            emp.get('legal_name'),
            emp.get('preferred_first_name'),
            emp.get('preferred_last_name'),
            emp.get('position_id'),
            emp.get('hire_date'),
            emp.get('job_title'),
            emp.get('position_start_date'),
            emp.get('position_status'),
            emp.get('location'),
            emp.get('work_email'),
        ))
        inserted += 1

    conn.commit()
    conn.close()

    return {
        'imported_count': inserted,
        'timestamp': timestamp
    }


def find_m365_users_not_in_adp(db_path: str) -> list[dict]:
    """
    Find M365 users not in ADP (orphaned licenses).

    Args:
        db_path: Path to SQLite database

    Returns:
        List of orphaned user dictionaries
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            ua.user_principal_name,
            ua.last_sign_in_date
        FROM user_activity ua
        LEFT JOIN adp_employees adp
            ON LOWER(ua.user_principal_name) = LOWER(adp.work_email)
        WHERE adp.work_email IS NULL
        ORDER BY ua.user_principal_name
    """)

    orphaned = []
    for row in cursor.fetchall():
        orphaned.append({
            'user_principal_name': row[0],
            'last_sign_in_date': row[1]
        })

    conn.close()
    return orphaned


def find_adp_users_inactive_in_m365(
    db_path: str,
    inactive_days: int = 90
) -> list[dict]:
    """
    Find ADP users who are inactive in M365.

    Args:
        db_path: Path to SQLite database
        inactive_days: Days threshold for inactivity

    Returns:
        List of inactive user dictionaries
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cutoff_date = (datetime.now() - timedelta(days=inactive_days)).isoformat()

    cursor.execute("""
        SELECT
            adp.work_email,
            adp.legal_name,
            adp.job_title,
            adp.position_status,
            adp.location,
            ua.last_sign_in_date
        FROM adp_employees adp
        LEFT JOIN user_activity ua
            ON LOWER(adp.work_email) = LOWER(ua.user_principal_name)
        WHERE adp.position_status = 'Active'
            AND (ua.last_sign_in_date IS NULL
                 OR ua.last_sign_in_date < ?)
        ORDER BY adp.legal_name
    """, (cutoff_date,))

    inactive = []
    for row in cursor.fetchall():
        inactive.append({
            'work_email': row[0],
            'legal_name': row[1],
            'job_title': row[2],
            'position_status': row[3],
            'location': row[4],
            'last_sign_in_date': row[5]
        })

    conn.close()
    return inactive


def find_terminated_with_licenses(db_path: str) -> list[dict]:
    """
    Find terminated ADP employees with active M365 licenses.

    Args:
        db_path: Path to SQLite database

    Returns:
        List of terminated employees with licenses
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            adp.work_email,
            adp.legal_name,
            adp.job_title,
            adp.position_status,
            adp.location,
            ua.last_sign_in_date
        FROM adp_employees adp
        INNER JOIN user_activity ua
            ON LOWER(adp.work_email) = LOWER(ua.user_principal_name)
        WHERE adp.position_status != 'Active'
        ORDER BY adp.legal_name
    """)

    terminated = []
    for row in cursor.fetchall():
        terminated.append({
            'work_email': row[0],
            'legal_name': row[1],
            'job_title': row[2],
            'position_status': row[3],
            'location': row[4],
            'last_sign_in_date': row[5]
        })

    conn.close()
    return terminated


def get_active_adp_count(db_path: str) -> int:
    """
    Get count of active employees in ADP.

    Args:
        db_path: Path to SQLite database

    Returns:
        Count of active employees
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM adp_employees
        WHERE position_status = 'Active'
    """)

    count = cursor.fetchone()[0]
    conn.close()
    return count


def generate_cross_reference_summary(db_path: str) -> dict:
    """
    Generate complete cross-reference summary.

    Args:
        db_path: Path to SQLite database

    Returns:
        Dictionary with summary statistics
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    summary = {}

    # ADP counts
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN position_status = 'Active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN position_status != 'Active' THEN 1 ELSE 0 END) as terminated
        FROM adp_employees
    """)
    row = cursor.fetchone()
    summary['adp_total_count'] = row[0] or 0
    summary['adp_active_count'] = row[1] or 0
    summary['adp_terminated_count'] = row[2] or 0

    # M365 user count
    cursor.execute("SELECT COUNT(DISTINCT user_principal_name) FROM user_activity")
    summary['m365_users_count'] = cursor.fetchone()[0] or 0

    conn.close()

    # Cross-reference counts
    summary['orphaned_licenses_count'] = len(find_m365_users_not_in_adp(db_path))
    summary['terminated_with_licenses_count'] = len(find_terminated_with_licenses(db_path))
    summary['inactive_users_count'] = len(find_adp_users_inactive_in_m365(db_path))

    return summary


def main():
    load_dotenv()

    db_path = os.getenv('DATABASE_PATH', './data/m365_costs.db')
    adp_file = sys.argv[1] if len(sys.argv) > 1 else None

    if not adp_file:
        print("Usage: python import_adp_data.py <adp_export.xlsx>")
        sys.exit(1)

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Run collect_m365_data.py first to collect M365 data.")
        sys.exit(1)

    print(f"Importing ADP data from {adp_file}...")
    print()

    result = import_adp_data(adp_file, db_path)

    print(f"✓ Imported {result['imported_count']} employees")
    print(f"  Timestamp: {result['timestamp']}")
    print()

    print("Generating cross-reference analysis...")
    print()

    summary = generate_cross_reference_summary(db_path)

    print("=" * 70)
    print("ADP vs M365 Cross-Reference Summary")
    print("=" * 70)
    print()
    print("ADP Data:")
    print(f"  Active employees: {summary['adp_active_count']:,}")
    print(f"  Terminated employees: {summary['adp_terminated_count']:,}")
    print(f"  Total in ADP: {summary['adp_total_count']:,}")
    print()
    print("M365 Data:")
    print(f"  Total M365 users: {summary['m365_users_count']:,}")
    print()
    print("Cross-Reference Issues:")
    print(f"  Orphaned licenses (M365 but not in ADP): {summary['orphaned_licenses_count']:,}")
    print(f"  Terminated with licenses: {summary['terminated_with_licenses_count']:,}")
    print(f"  Active but inactive 90+ days: {summary['inactive_users_count']:,}")
    print()

    # Show details for terminated with licenses
    if summary['terminated_with_licenses_count'] > 0:
        print("Terminated employees with M365 licenses:")
        terminated = find_terminated_with_licenses(db_path)
        for emp in terminated[:10]:  # Show first 10
            print(f"  - {emp['legal_name']} ({emp['work_email']})")
            print(f"    Status: {emp['position_status']}, Last sign-in: {emp['last_sign_in_date']}")
        if len(terminated) > 10:
            print(f"  ... and {len(terminated) - 10} more")
        print()

    # Show details for orphaned licenses
    if summary['orphaned_licenses_count'] > 0:
        print("M365 users not in ADP (orphaned licenses):")
        orphaned = find_m365_users_not_in_adp(db_path)
        for user in orphaned[:10]:  # Show first 10
            print(f"  - {user['user_principal_name']}")
            print(f"    Last sign-in: {user['last_sign_in_date']}")
        if len(orphaned) > 10:
            print(f"  ... and {len(orphaned) - 10} more")
        print()

    print("ADP import and analysis complete!")
    print("Run generate_dashboard.py to see full cross-reference report.")


if __name__ == '__main__':
    main()
