"""
Tests for incremental data collection with checkpoints and rate limiting.

Tests focus on:
- Checkpoint creation and recovery
- Batch processing for large datasets
- Rate limiting with retry logic
- Progress tracking
"""

import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

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
def large_user_list():
    """Generate large user list for batch testing."""
    users = []
    for i in range(500):
        users.append({
            "userPrincipalName": f"user{i:04d}@contoso.com",
            "signInActivity": {
                "lastSignInDateTime": datetime.now().isoformat() + 'Z'
            } if i % 2 == 0 else None
        })
    return users


@pytest.mark.unit
class TestCheckpointSystem:
    """Test checkpoint creation and recovery."""

    def test_create_checkpoint(self, temp_db):
        """Test creating a checkpoint during collection."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            create_checkpoint
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Create checkpoint
        create_checkpoint(
            temp_db,
            run_id,
            phase='user_licenses',
            progress=250,
            total=1000,
            details={'last_user': 'user0249@contoso.com'}
        )

        # Verify checkpoint was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT phase, progress, total, details
            FROM collection_checkpoints
            WHERE collection_run_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (run_id,))

        checkpoint = cursor.fetchone()
        assert checkpoint is not None
        assert checkpoint[0] == 'user_licenses'
        assert checkpoint[1] == 250
        assert checkpoint[2] == 1000
        conn.close()

    def test_get_latest_checkpoint(self, temp_db):
        """Test retrieving the most recent checkpoint."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            create_checkpoint,
            get_latest_checkpoint
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Create multiple checkpoints
        create_checkpoint(temp_db, run_id, 'users', 100, 1000, {})
        create_checkpoint(temp_db, run_id, 'users', 250, 1000, {})
        create_checkpoint(temp_db, run_id, 'user_licenses', 50, 500, {})

        # Get latest checkpoint
        checkpoint = get_latest_checkpoint(temp_db, run_id)

        assert checkpoint is not None
        assert checkpoint['phase'] == 'user_licenses'
        assert checkpoint['progress'] == 50
        assert checkpoint['total'] == 500

    def test_resume_from_checkpoint(self, temp_db):
        """Test resuming collection from a checkpoint."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            create_checkpoint,
            should_resume,
            get_latest_checkpoint
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Create checkpoint mid-collection
        create_checkpoint(
            temp_db,
            run_id,
            'user_licenses',
            250,
            1000,
            {'last_user': 'user0249@contoso.com'}
        )

        # Check if should resume
        can_resume = should_resume(temp_db, run_id)
        assert can_resume is True

        # Get checkpoint to resume from
        checkpoint = get_latest_checkpoint(temp_db, run_id)
        assert checkpoint['progress'] == 250
        assert checkpoint['details']['last_user'] == 'user0249@contoso.com'

    def test_no_checkpoint_to_resume(self, temp_db):
        """Test when there's no checkpoint to resume from."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            should_resume
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # No checkpoints created
        can_resume = should_resume(temp_db, run_id)
        assert can_resume is False


@pytest.mark.unit
class TestBatchProcessing:
    """Test batch processing for large datasets."""

    def test_process_users_in_batches(self, temp_db, large_user_list):
        """Test processing users in batches with checkpoints."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch,
            get_latest_checkpoint
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Process in batches of 100
        batch_size = 100
        total_users = len(large_user_list)

        for i in range(0, total_users, batch_size):
            batch = large_user_list[i:i + batch_size]
            store_user_activity_batch(
                temp_db,
                run_id,
                batch,
                batch_start=i,
                total_count=total_users
            )

        # Verify all users were stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM user_activity
            WHERE collection_run_id = ?
        """, (run_id,))
        count = cursor.fetchone()[0]
        assert count == total_users

        # Verify checkpoint exists for last batch
        checkpoint = get_latest_checkpoint(temp_db, run_id)
        assert checkpoint is not None
        assert checkpoint['progress'] == total_users
        conn.close()

    def test_resume_batch_processing(self, temp_db, large_user_list):
        """Test resuming batch processing after interruption."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch,
            get_latest_checkpoint
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        batch_size = 100
        total_users = len(large_user_list)

        # Process first 2 batches (200 users)
        for i in range(0, 200, batch_size):
            batch = large_user_list[i:i + batch_size]
            store_user_activity_batch(
                temp_db,
                run_id,
                batch,
                batch_start=i,
                total_count=total_users
            )

        # Simulate interruption - get checkpoint
        checkpoint = get_latest_checkpoint(temp_db, run_id)
        resume_from = checkpoint['progress']
        assert resume_from == 200

        # Resume from checkpoint
        for i in range(resume_from, total_users, batch_size):
            batch = large_user_list[i:i + batch_size]
            store_user_activity_batch(
                temp_db,
                run_id,
                batch,
                batch_start=i,
                total_count=total_users
            )

        # Verify all users processed
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM user_activity
            WHERE collection_run_id = ?
        """, (run_id,))
        count = cursor.fetchone()[0]
        assert count == total_users
        conn.close()


@pytest.mark.unit
class TestProgressTracking:
    """Test progress tracking and reporting."""

    def test_update_collection_progress(self, temp_db):
        """Test updating progress during collection."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            update_progress
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Update progress
        update_progress(
            temp_db,
            run_id,
            phase='users',
            progress=250,
            total=1000,
            message='Processing users batch 3/10'
        )

        # Verify progress stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT phase, progress, total, message
            FROM collection_progress
            WHERE collection_run_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (run_id,))

        progress = cursor.fetchone()
        assert progress[0] == 'users'
        assert progress[1] == 250
        assert progress[2] == 1000
        assert 'batch 3/10' in progress[3]
        conn.close()

    def test_get_collection_status(self, temp_db):
        """Test retrieving collection status."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            update_progress,
            get_collection_status
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Update progress multiple times
        update_progress(temp_db, run_id, 'users', 100, 1000, 'Batch 1')
        update_progress(temp_db, run_id, 'users', 250, 1000, 'Batch 2')
        update_progress(temp_db, run_id, 'user_licenses', 50, 500, 'Batch 1')

        # Get current status
        status = get_collection_status(temp_db, run_id)

        assert status['run_id'] == run_id
        assert status['current_phase'] == 'user_licenses'
        assert status['progress'] == 50
        assert status['total'] == 500
        assert status['percentage'] == 10.0


@pytest.mark.unit
class TestRateLimiting:
    """Test rate limiting detection and retry logic."""

    def test_detect_rate_limit(self):
        """Test detecting rate limit from response."""
        from scripts.collect_m365_data import is_rate_limited

        # Mock response object
        class MockResponse:
            def __init__(self, status_code, headers=None):
                self.status_code = status_code
                self.headers = headers or {}

        # Test 429 response
        response_429 = MockResponse(429, {'Retry-After': '60'})
        assert is_rate_limited(response_429) is True

        # Test normal response
        response_200 = MockResponse(200)
        assert is_rate_limited(response_200) is False

    def test_calculate_retry_delay(self):
        """Test calculating retry delay with exponential backoff."""
        from scripts.collect_m365_data import calculate_retry_delay

        # Test with Retry-After header
        class MockResponse:
            def __init__(self, headers):
                self.headers = headers

        response = MockResponse({'Retry-After': '60'})
        delay = calculate_retry_delay(response, attempt=0)
        assert delay == 60

        # Test exponential backoff without header
        response_no_header = MockResponse({})
        delay_1 = calculate_retry_delay(response_no_header, attempt=0)
        delay_2 = calculate_retry_delay(response_no_header, attempt=1)
        delay_3 = calculate_retry_delay(response_no_header, attempt=2)

        assert delay_1 == 1
        assert delay_2 == 2
        assert delay_3 == 4

    def test_retry_with_backoff(self, temp_db):
        """Test retry logic with exponential backoff."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            log_retry_attempt
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        # Log retry attempts
        log_retry_attempt(
            temp_db,
            run_id,
            endpoint='/users',
            attempt=1,
            delay=1,
            reason='Rate limited'
        )
        log_retry_attempt(
            temp_db,
            run_id,
            endpoint='/users',
            attempt=2,
            delay=2,
            reason='Rate limited'
        )

        # Verify retries logged
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM retry_log
            WHERE collection_run_id = ?
        """, (run_id,))
        count = cursor.fetchone()[0]
        assert count == 2
        conn.close()


@pytest.mark.integration
class TestIncrementalWorkflow:
    """Integration tests for complete incremental collection workflow."""

    def test_full_incremental_collection(self, temp_db, large_user_list):
        """Test complete incremental collection with checkpoints."""
        from scripts.collect_m365_data import (
            create_database_schema,
            start_collection_run,
            store_user_activity_batch,
            get_collection_status,
            complete_collection_run
        )

        create_database_schema(temp_db)
        run_id = start_collection_run(temp_db)

        batch_size = 100
        total_users = len(large_user_list)
        batches_processed = 0

        # Process all users in batches
        for i in range(0, total_users, batch_size):
            batch = large_user_list[i:i + batch_size]
            store_user_activity_batch(
                temp_db,
                run_id,
                batch,
                batch_start=i,
                total_count=total_users
            )
            batches_processed += 1

        # Check final status
        status = get_collection_status(temp_db, run_id)
        assert status['progress'] == total_users
        assert status['percentage'] == 100.0

        # Complete run
        complete_collection_run(
            temp_db,
            run_id,
            success=True,
            records=total_users
        )

        # Verify completion
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, records_collected
            FROM collection_runs
            WHERE id = ?
        """, (run_id,))
        status_row, records = cursor.fetchone()
        assert status_row == 'completed'
        assert records == total_users
        conn.close()
