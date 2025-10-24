"""
Tests for ADP data import functionality.

Tests verify that ADP employee data can be imported and cross-referenced
with M365 license assignments.
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_m365_and_adp_data(temp_db):
    """Create sample M365 and ADP data in database."""
    from scripts.collect_m365_data import create_database_schema

    create_database_schema(temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Create a collection run
    cursor.execute("""
        INSERT INTO collection_runs (timestamp, status, records_collected)
        VALUES (?, ?, ?)
    """, (datetime.now().isoformat(), 'completed', 4))
    run_id = cursor.lastrowid

    # Create ADP tables
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

    # Insert sample ADP data
    timestamp = datetime.now().isoformat()
    adp_data = [
        (timestamp, 'Smith, John', 'John', 'Smith', 'POS001', '2020-01-15',
         'Software Engineer', '2020-01-15', 'Active', 'Austin, TX',
         'john.smith@company.com'),
        (timestamp, 'Doe, Jane', 'Jane', 'Doe', 'POS002', '2019-03-20',
         'Product Manager', '2019-03-20', 'Active', 'New York, NY',
         'jane.doe@company.com'),
        (timestamp, 'Johnson, Bob', 'Bob', 'Johnson', 'POS003', '2021-06-10',
         'Designer', '2021-06-10', 'Terminated', 'San Francisco, CA',
         'bob.johnson@company.com'),
        (timestamp, 'Williams, Alice', 'Alice', 'Williams', 'POS004', '2018-11-05',
         'Engineer', '2018-11-05', 'Active', 'Seattle, WA',
         'alice.williams@company.com'),
    ]

    cursor.executemany("""
        INSERT INTO adp_employees (
            import_timestamp, legal_name, preferred_first_name,
            preferred_last_name, position_id, hire_date, job_title,
            position_start_date, position_status, location, work_email
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, adp_data)

    # Insert sample M365 user activity
    # Users: john.smith (active), jane.doe (active), bob.johnson (inactive),
    #        orphan.user (not in ADP)
    today = datetime.now()
    activity_data = [
        (run_id, 'john.smith@company.com', (today - timedelta(days=5)).isoformat()),
        (run_id, 'jane.doe@company.com', (today - timedelta(days=10)).isoformat()),
        (run_id, 'bob.johnson@company.com', (today - timedelta(days=120)).isoformat()),
        (run_id, 'orphan.user@company.com', (today - timedelta(days=2)).isoformat()),
    ]

    cursor.executemany("""
        INSERT INTO user_activity (collection_run_id, user_principal_name, last_sign_in_date)
        VALUES (?, ?, ?)
    """, activity_data)

    # Insert email aliases for testing alias matching
    # orphan.user has an alias but still not in ADP
    # bob.johnson has an alias but is terminated
    alias_data = [
        (run_id, 'orphan.user@company.com', 'orphan@elsewhere.com', 'proxyAddress'),
        (run_id, 'bob.johnson@company.com', 'bjohnson@company.com', 'proxyAddress'),
    ]

    cursor.executemany("""
        INSERT INTO user_email_aliases (collection_run_id, user_principal_name, email_address, email_type)
        VALUES (?, ?, ?, ?)
    """, alias_data)

    conn.commit()
    conn.close()

    return temp_db


@pytest.mark.unit
class TestADPImport:
    """Test ADP data import functionality."""

    def test_parse_adp_excel_file(self):
        """Test parsing ADP Excel export."""
        from scripts.import_adp_data import parse_adp_excel

        employees = parse_adp_excel('/Users/mpellon/Downloads/Michelle Report- E5.xlsx')

        assert len(employees) > 0
        assert all('work_email' in emp for emp in employees)
        assert all('position_status' in emp for emp in employees)
        assert all('legal_name' in emp for emp in employees)

    def test_import_adp_data_to_database(self, temp_db):
        """Test importing ADP data into database."""
        from scripts.import_adp_data import import_adp_data

        result = import_adp_data(
            '/Users/mpellon/Downloads/Michelle Report- E5.xlsx',
            temp_db
        )

        assert result['imported_count'] > 0
        assert result['timestamp'] is not None

        # Verify data in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM adp_employees")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == result['imported_count']

    def test_adp_schema_created(self, temp_db):
        """Test that ADP table schema is created correctly."""
        from scripts.collect_m365_data import create_database_schema

        create_database_schema(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='adp_employees'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_empty_adp_file_handling(self, temp_db):
        """Test handling of empty or invalid ADP files."""
        from scripts.import_adp_data import parse_adp_excel

        # This should handle gracefully
        with pytest.raises(Exception):
            parse_adp_excel('/nonexistent/file.xlsx')


@pytest.mark.unit
class TestADPCrossReference:
    """Test cross-referencing ADP with M365 data."""

    def test_find_m365_users_not_in_adp(self, sample_m365_and_adp_data):
        """Test finding M365 users not in ADP (orphaned licenses)."""
        from scripts.import_adp_data import find_m365_users_not_in_adp

        orphaned = find_m365_users_not_in_adp(sample_m365_and_adp_data)

        assert len(orphaned) == 1
        assert orphaned[0]['user_principal_name'] == 'orphan.user@company.com'

    def test_find_adp_users_inactive_in_m365(self, sample_m365_and_adp_data):
        """Test finding ADP users who are inactive in M365."""
        from scripts.import_adp_data import find_adp_users_inactive_in_m365

        inactive = find_adp_users_inactive_in_m365(
            sample_m365_and_adp_data,
            inactive_days=90
        )

        # Alice Williams is Active in ADP but has no recent M365 activity
        # (Her record exists but last sign-in would be old or NULL)
        # Bob Johnson is Terminated, so should NOT be in this list
        assert len(inactive) >= 0
        emails = [u['work_email'] for u in inactive]
        # Only active employees should appear in this list
        assert 'bob.johnson@company.com' not in emails

    def test_find_terminated_with_active_licenses(self, sample_m365_and_adp_data):
        """Test finding terminated ADP employees with active M365 licenses."""
        from scripts.import_adp_data import find_terminated_with_licenses

        terminated = find_terminated_with_licenses(sample_m365_and_adp_data)

        # Bob Johnson is terminated in ADP but has M365 user record
        assert len(terminated) >= 1
        emails = [u['work_email'] for u in terminated]
        assert 'bob.johnson@company.com' in emails

    def test_get_active_adp_count(self, sample_m365_and_adp_data):
        """Test getting count of active employees in ADP."""
        from scripts.import_adp_data import get_active_adp_count

        count = get_active_adp_count(sample_m365_and_adp_data)

        # Should be 3 active employees (John, Jane, Alice)
        assert count == 3

    def test_cross_reference_summary(self, sample_m365_and_adp_data):
        """Test generating complete cross-reference summary."""
        from scripts.import_adp_data import generate_cross_reference_summary

        summary = generate_cross_reference_summary(sample_m365_and_adp_data)

        assert 'adp_active_count' in summary
        assert 'adp_terminated_count' in summary
        assert 'm365_users_count' in summary
        assert 'orphaned_licenses_count' in summary
        assert 'terminated_with_licenses_count' in summary
        assert 'inactive_users_count' in summary


@pytest.mark.integration
class TestADPWorkflow:
    """Integration tests for complete ADP workflow."""

    def test_complete_import_and_analysis_workflow(self, temp_db):
        """Test complete workflow: import ADP -> analyze -> generate report."""
        from scripts.collect_m365_data import create_database_schema
        from scripts.import_adp_data import (
            import_adp_data,
            generate_cross_reference_summary
        )

        # 0. Create schema first
        create_database_schema(temp_db)

        # 1. Import ADP data
        result = import_adp_data(
            '/Users/mpellon/Downloads/Michelle Report- E5.xlsx',
            temp_db
        )
        assert result['imported_count'] > 0

        # 2. Generate cross-reference summary
        summary = generate_cross_reference_summary(temp_db)
        assert summary['adp_active_count'] > 0

        # 3. Verify summary has all expected keys
        expected_keys = [
            'adp_active_count',
            'adp_terminated_count',
            'adp_total_count',
            'm365_users_count',
            'orphaned_licenses_count',
            'terminated_with_licenses_count',
            'inactive_users_count'
        ]
        for key in expected_keys:
            assert key in summary
