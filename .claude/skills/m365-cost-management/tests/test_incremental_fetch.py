"""
Tests for fully incremental fetch with immediate DB writes.

Tests verify that users are written to database during fetch,
not accumulated in memory first.
"""

import os
import sqlite3
import tempfile
from datetime import datetime

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
def mock_paginated_users():
    """
    Mock paginated user response - 3 pages of 100 users each.
    """
    pages = []
    for page_num in range(3):
        users = []
        for i in range(100):
            user_idx = (page_num * 100) + i
            users.append({
                "userPrincipalName": f"user{user_idx:04d}@contoso.com",
                "signInActivity": {
                    "lastSignInDateTime": datetime.now().isoformat() + 'Z'
                } if user_idx % 2 == 0 else None
            })

        pages.append({
            "value": users,
            "@odata.nextLink": f"https://graph.microsoft.com/v1.0/users?$skiptoken=page{page_num+1}" if page_num < 2 else None
        })

    return pages


@pytest.mark.unit
class TestIncrementalFetch:
    """Test incremental fetch with immediate DB writes."""

    def test_write_users_during_fetch(self, temp_db):
        """
        Test that users are written to DB during fetch, not after.

        This simulates fetching pages and verifies DB is updated
        after each page, not at the end.
        """
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Simulate fetching and writing page by page
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Page 1 - 100 users
        page1_users = [
            {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
            for i in range(100)
        ]
        store_user_activity_batch(temp_db, run_id, page1_users, 0, 300)

        # Check DB immediately - should have 100 users
        cursor.execute("""
            SELECT COUNT(*) FROM user_activity
            WHERE collection_run_id = ?
        """, (run_id,))
        count = cursor.fetchone()[0]
        assert count == 100, "Users should be in DB after page 1"

        # Page 2 - 100 more users
        page2_users = [
            {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
            for i in range(100, 200)
        ]
        store_user_activity_batch(temp_db, run_id, page2_users, 100, 300)

        # Check DB - should have 200 users now
        cursor.execute("""
            SELECT COUNT(*) FROM user_activity
            WHERE collection_run_id = ?
        """, (run_id,))
        count = cursor.fetchone()[0]
        assert count == 200, "Users should be in DB after page 2"

        conn.close()

    def test_checkpoint_during_fetch(self, temp_db):
        """
        Test that checkpoints are created during fetch phase.
        """
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch,
            get_latest_checkpoint
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Fetch page 1
        page1_users = [
            {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
            for i in range(100)
        ]
        store_user_activity_batch(temp_db, run_id, page1_users, 0, 300)

        # Check checkpoint exists
        checkpoint = get_latest_checkpoint(temp_db, run_id)
        assert checkpoint is not None
        assert checkpoint['phase'] == 'user_activity'
        assert checkpoint['progress'] == 100

        # Fetch page 2
        page2_users = [
            {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
            for i in range(100, 200)
        ]
        store_user_activity_batch(temp_db, run_id, page2_users, 100, 300)

        # Check checkpoint updated
        checkpoint = get_latest_checkpoint(temp_db, run_id)
        assert checkpoint['progress'] == 200

    def test_resume_fetch_from_checkpoint(self, temp_db):
        """
        Test resuming fetch from checkpoint after interruption.

        Simulates:
        1. Fetch pages 1-2
        2. Interruption
        3. Resume - should start from page 3
        """
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch,
            get_latest_checkpoint
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Initial fetch - pages 1-2
        for page_num in range(2):
            page_users = [
                {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
                for i in range(page_num * 100, (page_num + 1) * 100)
            ]
            store_user_activity_batch(
                temp_db,
                run_id,
                page_users,
                page_num * 100,
                300
            )

        # Check checkpoint
        checkpoint = get_latest_checkpoint(temp_db, run_id)
        assert checkpoint['progress'] == 200

        # Verify 200 users in DB
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM user_activity
            WHERE collection_run_id = ?
        """, (run_id,))
        count = cursor.fetchone()[0]
        assert count == 200

        # Resume - fetch page 3
        page3_users = [
            {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
            for i in range(200, 300)
        ]
        store_user_activity_batch(temp_db, run_id, page3_users, 200, 300)

        # Verify all 300 users now
        cursor.execute("""
            SELECT COUNT(*) FROM user_activity
            WHERE collection_run_id = ?
        """, (run_id,))
        count = cursor.fetchone()[0]
        assert count == 300

        conn.close()

    def test_no_duplicate_users_on_resume(self, temp_db):
        """
        Test that resuming doesn't create duplicate users.

        Uses INSERT OR REPLACE to handle duplicates.
        """
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Fetch page 1 twice (simulating interrupted resume)
        page1_users = [
            {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
            for i in range(100)
        ]

        # First time
        store_user_activity_batch(temp_db, run_id, page1_users, 0, 100)

        # Second time (should replace, not duplicate)
        store_user_activity_batch(temp_db, run_id, page1_users, 0, 100)

        # Check only 100 users (not 200)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM user_activity
            WHERE collection_run_id = ?
        """, (run_id,))
        count = cursor.fetchone()[0]
        assert count == 100, "Should not have duplicate users"
        conn.close()

    def test_progress_tracking_without_total(self, temp_db):
        """
        Test progress tracking when total is unknown initially.

        During fetch, we don't know total user count, but we can
        still track pages fetched.
        """
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch,
            get_collection_status
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Fetch with unknown total (use estimate)
        page1_users = [
            {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
            for i in range(100)
        ]

        # Pass -1 as total to indicate "unknown"
        store_user_activity_batch(temp_db, run_id, page1_users, 0, -1)

        # Status should handle unknown total gracefully
        status = get_collection_status(temp_db, run_id)
        assert status['progress'] == 100
        # Percentage might be 0 or undefined when total is -1

    def test_update_total_when_known(self, temp_db):
        """
        Test updating total count when it becomes known.

        After fetch completes, we know exact total and can update
        all checkpoints/progress entries.
        """
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch,
            get_collection_status
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Fetch pages with unknown total
        for page_num in range(3):
            page_users = [
                {"userPrincipalName": f"user{i:04d}@contoso.com", "signInActivity": None}
                for i in range(page_num * 100, (page_num + 1) * 100)
            ]
            # Use actual count for last page to set final total
            total = 300 if page_num == 2 else -1
            store_user_activity_batch(
                temp_db,
                run_id,
                page_users,
                page_num * 100,
                total
            )

        # Final status should have correct total
        status = get_collection_status(temp_db, run_id)
        assert status['progress'] == 300
        assert status['total'] == 300
        assert status['percentage'] == 100.0


@pytest.mark.integration
class TestIncrementalFetchWorkflow:
    """Integration tests for complete incremental fetch workflow."""

    def test_complete_incremental_fetch(self, temp_db):
        """
        Test complete fetch workflow with incremental writes.

        Simulates:
        1. Start collection
        2. Fetch 3 pages incrementally
        3. Each page writes to DB immediately
        4. Checkpoints created after each page
        5. Progress tracked throughout
        """
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch,
            get_latest_checkpoint,
            get_collection_status
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Simulate fetching 3 pages
        total_pages = 3
        users_per_page = 100

        for page_num in range(total_pages):
            # Create page of users
            page_users = [
                {
                    "userPrincipalName": f"user{i:04d}@contoso.com",
                    "signInActivity": {
                        "lastSignInDateTime": datetime.now().isoformat() + 'Z'
                    } if i % 2 == 0 else None
                }
                for i in range(page_num * users_per_page, (page_num + 1) * users_per_page)
            ]

            # Write to DB immediately
            total = total_pages * users_per_page if page_num == total_pages - 1 else -1
            store_user_activity_batch(
                temp_db,
                run_id,
                page_users,
                page_num * users_per_page,
                total
            )

            # Verify users in DB after each page
            cursor.execute("""
                SELECT COUNT(*) FROM user_activity
                WHERE collection_run_id = ?
            """, (run_id,))
            count = cursor.fetchone()[0]
            expected = (page_num + 1) * users_per_page
            assert count == expected, f"Should have {expected} users after page {page_num + 1}"

            # Verify checkpoint exists
            checkpoint = get_latest_checkpoint(temp_db, run_id)
            assert checkpoint is not None
            assert checkpoint['progress'] == expected

        # Final verification
        status = get_collection_status(temp_db, run_id)
        assert status['progress'] == 300
        assert status['total'] == 300
        assert status['percentage'] == 100.0

        conn.close()
