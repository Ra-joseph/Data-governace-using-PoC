"""
Unit tests for PostgresConnector service.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock, PropertyMock

from app.services.postgres_connector import PostgresConnector


@pytest.mark.unit
@pytest.mark.service
class TestPostgresConnectorInit:
    """Test PostgresConnector initialization."""

    @patch("app.services.postgres_connector.settings")
    def test_init_default_settings(self, mock_settings):
        """Test initialization with default settings."""
        mock_settings.POSTGRES_HOST = "localhost"
        mock_settings.POSTGRES_PORT = 5432
        mock_settings.POSTGRES_DB = "financial_demo"
        mock_settings.POSTGRES_USER = "governance_user"
        mock_settings.POSTGRES_PASSWORD = "governance_pass"

        connector = PostgresConnector()
        assert connector.host == "localhost"
        assert connector.port == 5432
        assert connector.database == "financial_demo"
        assert connector.user == "governance_user"
        assert connector.password == "governance_pass"
        assert connector.connection is None

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        connector = PostgresConnector(
            host="custom-host",
            port=5433,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        assert connector.host == "custom-host"
        assert connector.port == 5433
        assert connector.database == "test_db"
        assert connector.user == "test_user"
        assert connector.password == "test_pass"


@pytest.mark.unit
@pytest.mark.service
class TestPostgresConnectorConnection:
    """Test PostgresConnector connection management."""

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_connect_creates_connection(self, mock_connect):
        """Test that connect creates a new connection."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        result = connector.connect()

        assert result == mock_conn
        mock_connect.assert_called_once()

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_connect_reuses_open_connection(self, mock_connect):
        """Test that an existing open connection is reused."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        conn1 = connector.connect()
        conn2 = connector.connect()

        assert conn1 == conn2
        assert mock_connect.call_count == 1

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_connect_reconnects_closed(self, mock_connect):
        """Test that a closed connection triggers reconnection."""
        mock_conn_old = MagicMock()
        mock_conn_old.closed = True
        mock_conn_new = MagicMock()
        mock_conn_new.closed = False

        mock_connect.return_value = mock_conn_new

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        connector.connection = mock_conn_old
        conn = connector.connect()

        # Should have created a new connection since old was closed
        assert conn == mock_conn_new
        assert mock_connect.call_count == 1

    def test_disconnect_closes_connection(self):
        """Test that disconnect closes an open connection."""
        mock_conn = MagicMock()
        mock_conn.closed = False

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        connector.connection = mock_conn
        connector.disconnect()

        mock_conn.close.assert_called_once()

    def test_disconnect_already_closed(self):
        """Test that disconnect is a no-op when connection is closed."""
        mock_conn = MagicMock()
        mock_conn.closed = True

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        connector.connection = mock_conn
        connector.disconnect()

        mock_conn.close.assert_not_called()

    def test_disconnect_no_connection(self):
        """Test that disconnect is a no-op when no connection exists."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        connector.disconnect()  # Should not raise


@pytest.mark.unit
@pytest.mark.service
class TestPostgresConnectorTestConnection:
    """Test PostgresConnector test_connection method."""

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_test_connection_success(self, mock_connect):
        """Test successful connection test."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        assert connector.test_connection() is True
        mock_cursor.execute.assert_called_once_with("SELECT 1")

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_test_connection_failure(self, mock_connect):
        """Test failed connection test returns False."""
        mock_connect.side_effect = Exception("Connection refused")

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        assert connector.test_connection() is False


@pytest.mark.unit
@pytest.mark.service
class TestPostgresConnectorListTables:
    """Test PostgresConnector table listing."""

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_list_tables_success(self, mock_connect):
        """Test successful table listing."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"table_name": "customers", "table_schema": "public", "table_type": "BASE TABLE"},
            {"table_name": "orders", "table_schema": "public", "table_type": "BASE TABLE"}
        ]
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        tables = connector.list_tables()

        assert len(tables) == 2
        assert tables[0]["table_name"] == "customers"

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_list_tables_empty_schema(self, mock_connect):
        """Test listing tables when schema has no tables."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        tables = connector.list_tables()
        assert tables == []

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_list_tables_connection_error(self, mock_connect):
        """Test that connection error raises exception."""
        mock_connect.side_effect = Exception("Connection refused")

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        with pytest.raises(Exception, match="Failed to list tables"):
            connector.list_tables()


@pytest.mark.unit
@pytest.mark.service
class TestPostgresConnectorPIIDetection:
    """Test PostgresConnector PII field detection."""

    def test_is_pii_field_exact_match(self):
        """Test PII detection with exact keyword match."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        assert connector._is_pii_field("email") is True
        assert connector._is_pii_field("ssn") is True
        assert connector._is_pii_field("phone") is True

    def test_is_pii_field_substring_match(self):
        """Test PII detection with substring match."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        assert connector._is_pii_field("customer_email_address") is True
        assert connector._is_pii_field("home_address") is True
        assert connector._is_pii_field("phone_number") is True

    def test_is_pii_field_case_insensitive(self):
        """Test PII detection is case-insensitive."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        assert connector._is_pii_field("EMAIL") is True
        assert connector._is_pii_field("Social_Security") is True
        assert connector._is_pii_field("Credit_Card") is True

    def test_is_pii_field_non_pii(self):
        """Test non-PII fields return False."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        assert connector._is_pii_field("created_at") is False
        assert connector._is_pii_field("amount") is False
        assert connector._is_pii_field("status") is False
        assert connector._is_pii_field("id") is False

    def test_is_pii_field_all_keywords(self):
        """Test each PII keyword is detected."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        for keyword in PostgresConnector.PII_KEYWORDS:
            assert connector._is_pii_field(keyword) is True, f"Expected '{keyword}' to be PII"


@pytest.mark.unit
@pytest.mark.service
class TestPostgresConnectorTypeMapping:
    """Test PostgresConnector type mapping."""

    def test_map_type_all_mappings(self):
        """Test all type mappings produce correct generic types."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        # String types
        assert connector._map_type("character varying") == "string"
        assert connector._map_type("varchar") == "string"
        assert connector._map_type("text") == "string"

        # Integer types
        assert connector._map_type("integer") == "integer"
        assert connector._map_type("bigint") == "integer"
        assert connector._map_type("smallint") == "integer"

        # Float types
        assert connector._map_type("numeric") == "float"
        assert connector._map_type("double precision") == "float"
        assert connector._map_type("real") == "float"

        # Boolean types
        assert connector._map_type("boolean") == "boolean"
        assert connector._map_type("bool") == "boolean"

        # Date/time types
        assert connector._map_type("date") == "date"
        assert connector._map_type("timestamp") == "timestamp"
        assert connector._map_type("timestamptz") == "timestamp"

        # JSON types
        assert connector._map_type("json") == "json"
        assert connector._map_type("jsonb") == "json"

    def test_map_type_unknown_defaults_string(self):
        """Test that unknown types default to 'string'."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        assert connector._map_type("uuid") == "string"
        assert connector._map_type("bytea") == "string"
        assert connector._map_type("cidr") == "string"

    def test_map_type_case_insensitive(self):
        """Test that type mapping is case-insensitive."""
        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        assert connector._map_type("INTEGER") == "integer"
        assert connector._map_type("VARCHAR") == "string"
        assert connector._map_type("Boolean") == "boolean"


@pytest.mark.unit
@pytest.mark.service
class TestPostgresConnectorStatistics:
    """Test PostgresConnector table statistics."""

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_get_table_statistics_success(self, mock_connect):
        """Test successful statistics retrieval."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"row_count": 1000},
            {"total_size": "45 MB"}
        ]
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        stats = connector.get_table_statistics("customers")

        assert stats["row_count"] == 1000
        assert stats["total_size"] == "45 MB"

    @patch("app.services.postgres_connector.psycopg2.connect")
    def test_get_table_statistics_error(self, mock_connect):
        """Test that errors return default statistics with error key."""
        mock_connect.side_effect = Exception("Connection refused")

        connector = PostgresConnector(
            host="localhost", port=5432, database="test",
            user="user", password="pass"
        )
        stats = connector.get_table_statistics("nonexistent_table")

        assert stats["row_count"] == 0
        assert stats["total_size"] == "Unknown"
        assert "error" in stats
