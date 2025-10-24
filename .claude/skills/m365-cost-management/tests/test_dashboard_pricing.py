"""
Tests for dashboard pricing functionality.

Tests verify that pricing data can be retrieved, displayed, edited,
and exported as SQL statements.
"""

import os
import sqlite3
import tempfile

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
def sample_pricing_data(temp_db):
    """Create sample pricing data in database."""
    from scripts.collect_m365_data import create_database_schema

    create_database_schema(temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Insert sample pricing data
    pricing_data = [
        ('12345-abcde', 'MICROSOFT 365 E3', 36.00),
        ('67890-fghij', 'MICROSOFT 365 E5', 57.00),
        ('11111-aaaaa', 'OFFICE 365 E1', 8.00),
        ('22222-bbbbb', 'POWER BI PRO', 9.99),
        ('33333-ccccc', 'AZURE AD PREMIUM P1', 6.00),
    ]

    cursor.executemany("""
        INSERT INTO price_lookup (sku_id, sku_name, monthly_cost)
        VALUES (?, ?, ?)
    """, pricing_data)

    conn.commit()
    conn.close()

    return pricing_data


@pytest.mark.unit
class TestPricingData:
    """Test pricing data retrieval."""

    def test_get_all_pricing_data(self, temp_db, sample_pricing_data):
        """Test retrieving all pricing data from database."""
        from scripts.generate_dashboard import get_pricing_data

        pricing = get_pricing_data(temp_db)

        assert len(pricing) == 5
        assert all('sku_id' in item for item in pricing)
        assert all('sku_name' in item for item in pricing)
        assert all('monthly_cost' in item for item in pricing)

    def test_pricing_data_sorted_by_name(self, temp_db, sample_pricing_data):
        """Test that pricing data is sorted alphabetically by SKU name."""
        from scripts.generate_dashboard import get_pricing_data

        pricing = get_pricing_data(temp_db)

        names = [item['sku_name'] for item in pricing]
        assert names == sorted(names)

    def test_pricing_data_includes_all_fields(self, temp_db, sample_pricing_data):
        """Test that each pricing record has all required fields."""
        from scripts.generate_dashboard import get_pricing_data

        pricing = get_pricing_data(temp_db)

        for item in pricing:
            assert 'sku_id' in item
            assert 'sku_name' in item
            assert 'monthly_cost' in item
            assert isinstance(item['monthly_cost'], (int, float))

    def test_empty_pricing_table(self, temp_db):
        """Test handling of empty pricing table."""
        from scripts.collect_m365_data import create_database_schema
        from scripts.generate_dashboard import get_pricing_data

        create_database_schema(temp_db)
        pricing = get_pricing_data(temp_db)

        assert pricing == []


@pytest.mark.unit
class TestPricingSQLGeneration:
    """Test SQL generation for price updates."""

    def test_generate_update_sql_single_price(self):
        """Test generating SQL for single price update."""
        from scripts.generate_dashboard import generate_pricing_update_sql

        changes = [
            {'sku_id': '12345-abcde', 'sku_name': 'MICROSOFT 365 E3', 'monthly_cost': 40.00}
        ]

        sql = generate_pricing_update_sql(changes)

        assert "UPDATE price_lookup" in sql
        assert "SET monthly_cost = 40.0" in sql
        assert "WHERE sku_id = '12345-abcde'" in sql

    def test_generate_update_sql_multiple_prices(self):
        """Test generating SQL for multiple price updates."""
        from scripts.generate_dashboard import generate_pricing_update_sql

        changes = [
            {'sku_id': '12345-abcde', 'sku_name': 'MICROSOFT 365 E3', 'monthly_cost': 40.00},
            {'sku_id': '67890-fghij', 'sku_name': 'MICROSOFT 365 E5', 'monthly_cost': 60.00},
        ]

        sql = generate_pricing_update_sql(changes)

        assert sql.count("UPDATE price_lookup") == 2
        assert "40.0" in sql
        assert "60.0" in sql
        assert "12345-abcde" in sql
        assert "67890-fghij" in sql

    def test_generate_update_sql_with_comments(self):
        """Test that generated SQL includes helpful comments."""
        from scripts.generate_dashboard import generate_pricing_update_sql

        changes = [
            {'sku_id': '12345-abcde', 'sku_name': 'MICROSOFT 365 E3', 'monthly_cost': 40.00}
        ]

        sql = generate_pricing_update_sql(changes)

        assert "-- Update pricing for MICROSOFT 365 E3" in sql or "MICROSOFT 365 E3" in sql

    def test_generate_update_sql_empty_changes(self):
        """Test generating SQL with no changes."""
        from scripts.generate_dashboard import generate_pricing_update_sql

        changes = []
        sql = generate_pricing_update_sql(changes)

        assert sql == "" or "-- No pricing changes" in sql


@pytest.mark.integration
class TestPricingWorkflow:
    """Integration tests for complete pricing workflow."""

    def test_retrieve_edit_export_workflow(self, temp_db, sample_pricing_data):
        """Test complete workflow: retrieve -> edit -> export SQL."""
        from scripts.generate_dashboard import (
            get_pricing_data,
            generate_pricing_update_sql
        )

        # 1. Retrieve current pricing
        pricing = get_pricing_data(temp_db)
        assert len(pricing) == 5

        # 2. Simulate editing a price
        edited_pricing = pricing.copy()
        for item in edited_pricing:
            if item['sku_name'] == 'MICROSOFT 365 E3':
                item['monthly_cost'] = 40.00  # Changed from 36.00

        # 3. Generate SQL for changes
        changes = [item for item in edited_pricing if item['sku_name'] == 'MICROSOFT 365 E3']
        sql = generate_pricing_update_sql(changes)

        # 4. Verify SQL is valid
        assert "UPDATE price_lookup" in sql
        assert "40.0" in sql

    def test_apply_sql_updates_to_database(self, temp_db, sample_pricing_data):
        """Test that generated SQL actually updates the database."""
        from scripts.generate_dashboard import (
            get_pricing_data,
            generate_pricing_update_sql
        )

        # Get original price
        pricing = get_pricing_data(temp_db)
        e3_original = next(p for p in pricing if p['sku_name'] == 'MICROSOFT 365 E3')
        assert e3_original['monthly_cost'] == 36.00

        # Generate update SQL
        changes = [
            {'sku_id': '12345-abcde', 'sku_name': 'MICROSOFT 365 E3', 'monthly_cost': 40.00}
        ]
        sql = generate_pricing_update_sql(changes)

        # Apply SQL to database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.executescript(sql)
        conn.commit()
        conn.close()

        # Verify price was updated
        pricing_after = get_pricing_data(temp_db)
        e3_updated = next(p for p in pricing_after if p['sku_name'] == 'MICROSOFT 365 E3')
        assert e3_updated['monthly_cost'] == 40.00
