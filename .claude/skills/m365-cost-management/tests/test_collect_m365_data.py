"""
Tests for M365 data collection script.

Tests use real Microsoft Graph API response structures but don't
mock API calls (per Michelle's rules - no mocks, use real data/APIs).
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_skus():
    """Sample subscribedSkus response from Graph API."""
    return {
        "value": [
            {
                "id": "6fd2c87f-b296-42f0-b197-1e91e994b900_c7df2760-2c81-4ef7-b578-5b5392b571df",
                "skuId": "c7df2760-2c81-4ef7-b578-5b5392b571df",
                "skuPartNumber": "ENTERPRISEPREMIUM",
                "prepaidUnits": {
                    "enabled": 100,
                    "suspended": 0,
                    "warning": 0
                },
                "consumedUnits": 75
            },
            {
                "id": "6fd2c87f-b296-42f0-b197-1e91e994b900_18181a46-0d4e-45cd-891e-60aabd171b4e",
                "skuId": "18181a46-0d4e-45cd-891e-60aabd171b4e",
                "skuPartNumber": "ENTERPRISEPACK",
                "prepaidUnits": {
                    "enabled": 50,
                    "suspended": 0,
                    "warning": 0
                },
                "consumedUnits": 50
            }
        ]
    }


@pytest.fixture
def sample_users():
    """Sample users response with sign-in activity from Graph API."""
    ninety_days_ago = (datetime.now() - timedelta(days=90)).isoformat() + 'Z'
    return {
        "value": [
            {
                "userPrincipalName": "active.user@contoso.com",
                "signInActivity": {
                    "lastSignInDateTime": datetime.now().isoformat() + 'Z'
                }
            },
            {
                "userPrincipalName": "inactive.user@contoso.com",
                "signInActivity": {
                    "lastSignInDateTime": ninety_days_ago
                }
            },
            {
                "userPrincipalName": "never.signed.in@contoso.com",
                "signInActivity": None
            }
        ]
    }


@pytest.fixture
def sample_user_licenses():
    """Sample user license details from Graph API."""
    return {
        "active.user@contoso.com": {
            "value": [
                {
                    "skuId": "c7df2760-2c81-4ef7-b578-5b5392b571df",
                    "skuPartNumber": "ENTERPRISEPREMIUM"
                }
            ]
        },
        "inactive.user@contoso.com": {
            "value": [
                {
                    "skuId": "18181a46-0d4e-45cd-891e-60aabd171b4e",
                    "skuPartNumber": "ENTERPRISEPACK"
                }
            ]
        }
    }


@pytest.mark.unit
class TestDatabaseOperations:
    """Test database schema creation and operations."""

    def test_create_database_schema(self, temp_db):
        """Test that database schema is created correctly."""
        from scripts.collect_m365_data import create_database_schema

        create_database_schema(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check all tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        assert 'collection_runs' in tables
        assert 'licenses' in tables
        assert 'price_lookup' in tables
        assert 'user_licenses' in tables
        assert 'user_activity' in tables

        conn.close()

    def test_start_collection_run(self, temp_db):
        """Test starting a new collection run."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        assert isinstance(run_id, int)
        assert run_id > 0

        # Verify run was created with 'running' status
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status FROM collection_runs WHERE id = ?
        """, (run_id,))
        status = cursor.fetchone()[0]
        assert status == 'running'
        conn.close()

    def test_complete_collection_run_success(self, temp_db):
        """Test completing a collection run successfully."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            complete_collection_run
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)
        complete_collection_run(temp_db, run_id, success=True, records=100)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, records_collected
            FROM collection_runs
            WHERE id = ?
        """, (run_id,))
        status, records = cursor.fetchone()

        assert status == 'completed'
        assert records == 100
        conn.close()

    def test_complete_collection_run_failure(self, temp_db):
        """Test completing a collection run with failure."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            complete_collection_run
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)
        complete_collection_run(
            temp_db,
            run_id,
            success=False,
            error_message="Test error"
        )

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, error_message
            FROM collection_runs
            WHERE id = ?
        """, (run_id,))
        status, error = cursor.fetchone()

        assert status == 'failed'
        assert error == "Test error"
        conn.close()


@pytest.mark.unit
class TestDataProcessing:
    """Test processing of Graph API responses."""

    def test_store_licenses(self, temp_db, sample_skus):
        """Test storing license data from Graph API response."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_licenses
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        store_licenses(temp_db, run_id, sample_skus['value'])

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sku_id, sku_name, total_licenses, assigned_licenses, available_licenses
            FROM licenses
            WHERE collection_run_id = ?
            ORDER BY sku_name
        """, (run_id,))
        licenses = cursor.fetchall()

        assert len(licenses) == 2

        # Check first license
        assert licenses[0][0] == "18181a46-0d4e-45cd-891e-60aabd171b4e"
        assert licenses[0][1] == "ENTERPRISEPACK"
        assert licenses[0][2] == 50  # total
        assert licenses[0][3] == 50  # assigned
        assert licenses[0][4] == 0   # available

        # Check second license
        assert licenses[1][0] == "c7df2760-2c81-4ef7-b578-5b5392b571df"
        assert licenses[1][1] == "ENTERPRISEPREMIUM"
        assert licenses[1][2] == 100  # total
        assert licenses[1][3] == 75   # assigned
        assert licenses[1][4] == 25   # available

        conn.close()

    def test_store_user_activity(self, temp_db, sample_users):
        """Test storing user activity from Graph API response."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        store_user_activity(temp_db, run_id, sample_users['value'])

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_principal_name, last_sign_in_date
            FROM user_activity
            WHERE collection_run_id = ?
            ORDER BY user_principal_name
        """, (run_id,))
        activity = cursor.fetchall()

        assert len(activity) == 3

        # Check active user has recent sign-in
        assert activity[0][0] == "active.user@contoso.com"
        assert activity[0][1] is not None

        # Check inactive user has old sign-in
        assert activity[1][0] == "inactive.user@contoso.com"
        assert activity[1][1] is not None

        # Check never-signed-in user has null
        assert activity[2][0] == "never.signed.in@contoso.com"
        assert activity[2][1] is None

        conn.close()

    def test_store_user_licenses(self, temp_db, sample_user_licenses):
        """Test storing user license assignments."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_licenses
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        store_user_licenses(temp_db, run_id, sample_user_licenses)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_principal_name, sku_id
            FROM user_licenses
            WHERE collection_run_id = ?
            ORDER BY user_principal_name
        """, (run_id,))
        user_licenses = cursor.fetchall()

        assert len(user_licenses) == 2

        # Check active user license
        assert user_licenses[0][0] == "active.user@contoso.com"
        assert user_licenses[0][1] == "c7df2760-2c81-4ef7-b578-5b5392b571df"

        # Check inactive user license
        assert user_licenses[1][0] == "inactive.user@contoso.com"
        assert user_licenses[1][1] == "18181a46-0d4e-45cd-891e-60aabd171b4e"

        conn.close()


@pytest.mark.unit
class TestPriceLookup:
    """Test price lookup functionality."""

    def test_initialize_default_prices(self, temp_db):
        """Test initialization of default price lookup data."""
        from scripts.collect_m365_data import (
            create_database_schema,
            initialize_default_prices
        )

        create_database_schema(temp_db)
        initialize_default_prices(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM price_lookup")
        count = cursor.fetchone()[0]

        # Should have at least some default prices
        assert count > 0

        # Check that prices are non-negative
        cursor.execute("""
            SELECT MIN(monthly_cost), MAX(monthly_cost)
            FROM price_lookup
        """)
        min_cost, max_cost = cursor.fetchone()
        assert min_cost >= 0
        assert max_cost > 0

        conn.close()


@pytest.mark.integration
class TestFullWorkflow:
    """Integration tests for complete data collection workflow."""

    def test_complete_collection_workflow(
        self,
        temp_db,
        sample_skus,
        sample_users,
        sample_user_licenses
    ):
        """Test complete data collection and storage workflow."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_licenses,
            store_user_activity,
            store_user_licenses,
            complete_collection_run,
            initialize_default_prices
        )

        # Setup
        create_database_schema(temp_db)
        initialize_default_prices(temp_db)
        run_id = start_collection_run(temp_db)

        # Collect and store data
        store_licenses(temp_db, run_id, sample_skus['value'])
        store_user_activity(temp_db, run_id, sample_users['value'])
        store_user_licenses(temp_db, run_id, sample_user_licenses)

        # Complete run
        total_records = (
            len(sample_skus['value']) +
            len(sample_users['value']) +
            len(sample_user_licenses)
        )
        complete_collection_run(
            temp_db,
            run_id,
            success=True,
            records=total_records
        )

        # Verify complete state
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check run completed successfully
        cursor.execute("""
            SELECT status, records_collected
            FROM collection_runs
            WHERE id = ?
        """, (run_id,))
        status, records = cursor.fetchone()
        assert status == 'completed'
        assert records == total_records

        # Check all data is queryable together
        cursor.execute("""
            SELECT
                ua.user_principal_name,
                l.sku_name,
                ua.last_sign_in_date,
                p.monthly_cost
            FROM user_licenses ul
            INNER JOIN user_activity ua
                ON ul.user_principal_name = ua.user_principal_name
            INNER JOIN licenses l
                ON ul.sku_id = l.sku_id
            LEFT JOIN price_lookup p
                ON ul.sku_id = p.sku_id
            WHERE ul.collection_run_id = ?
            ORDER BY ua.user_principal_name
        """, (run_id,))

        results = cursor.fetchall()
        assert len(results) == 2  # Two users with licenses

        conn.close()
