import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional, Tuple
from app.schemas.dataset import FieldSchema, FieldType
from app.config import settings


class PostgresConnector:
    """Connector for importing schemas from PostgreSQL databases."""
    
    # PII detection keywords
    PII_KEYWORDS = [
        'email', 'ssn', 'social_security', 'phone', 'address', 
        'credit_card', 'passport', 'driver_license', 'birth_date', 
        'dob', 'date_of_birth', 'maiden_name'
    ]
    
    # PostgreSQL to generic type mapping
    TYPE_MAPPING = {
        'character varying': 'string',
        'varchar': 'string',
        'character': 'string',
        'char': 'string',
        'text': 'string',
        'integer': 'integer',
        'int': 'integer',
        'int4': 'integer',
        'smallint': 'integer',
        'int2': 'integer',
        'bigint': 'integer',
        'int8': 'integer',
        'decimal': 'float',
        'numeric': 'float',
        'real': 'float',
        'float4': 'float',
        'double precision': 'float',
        'float8': 'float',
        'boolean': 'boolean',
        'bool': 'boolean',
        'date': 'date',
        'timestamp': 'timestamp',
        'timestamp without time zone': 'timestamp',
        'timestamp with time zone': 'timestamp',
        'timestamptz': 'timestamp',
        'time': 'timestamp',
        'json': 'json',
        'jsonb': 'json'
    }
    
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None):
        """Initialize PostgreSQL connector."""
        self.host = host or settings.POSTGRES_HOST
        self.port = port or settings.POSTGRES_PORT
        self.database = database or settings.POSTGRES_DB
        self.user = user or settings.POSTGRES_USER
        self.password = password or settings.POSTGRES_PASSWORD
        self.connection = None
    
    def connect(self):
        """Establish database connection."""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
        return self.connection
    
    def disconnect(self):
        """Close database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
        finally:
            self.disconnect()
    
    def list_tables(self, schema: str = 'public') -> List[Dict[str, Any]]:
        """
        List all tables in the specified schema.
        
        Args:
            schema: Database schema name
            
        Returns:
            List of table information
        """
        try:
            conn = self.connect()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    table_name,
                    table_schema,
                    table_type
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
            """
            
            cursor.execute(query, (schema,))
            tables = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in tables]
        
        except Exception as e:
            raise Exception(f"Failed to list tables: {e}")
        finally:
            self.disconnect()
    
    def import_table_schema(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """
        Import complete schema definition from a PostgreSQL table.
        
        Args:
            table_name: Name of the table
            schema: Database schema name
            
        Returns:
            Dictionary containing schema definition and metadata
        """
        try:
            conn = self.connect()
            
            # Get column information
            columns = self._get_columns(conn, table_name, schema)
            
            # Get primary keys
            primary_keys = self._get_primary_keys(conn, table_name, schema)
            
            # Get foreign keys
            foreign_keys = self._get_foreign_keys(conn, table_name, schema)
            
            # Get indexes
            indexes = self._get_indexes(conn, table_name, schema)
            
            # Get table comment/description
            table_comment = self._get_table_comment(conn, table_name, schema)
            
            # Get table statistics
            statistics = self.get_table_statistics(table_name, schema)
            
            # Build schema definition
            schema_definition = []
            contains_pii = False
            
            for col in columns:
                # Detect PII
                is_pii = self._is_pii_field(col['column_name'])
                if is_pii:
                    contains_pii = True
                
                # Map PostgreSQL type to generic type
                generic_type = self._map_type(col['data_type'])
                
                field = FieldSchema(
                    name=col['column_name'],
                    type=FieldType(generic_type),
                    required=col['is_nullable'] == 'NO',
                    nullable=col['is_nullable'] == 'YES',
                    pii=is_pii,
                    description=col.get('column_comment') or (
                        f"{col['column_name'].replace('_', ' ').title()}" +
                        (" - SENSITIVE DATA" if is_pii else "")
                    ),
                    max_length=col.get('character_maximum_length'),
                    foreign_key=foreign_keys.get(col['column_name'])
                )
                
                schema_definition.append(field)
            
            # Suggest classification based on PII presence
            suggested_classification = 'confidential' if contains_pii else 'internal'
            
            return {
                'table_name': table_name,
                'schema_name': schema,
                'description': table_comment or f"{table_name.replace('_', ' ').title()} table" + 
                              (" - CONTAINS PII" if contains_pii else ""),
                'schema_definition': [field.dict() for field in schema_definition],
                'metadata': {
                    'contains_pii': contains_pii,
                    'suggested_classification': suggested_classification,
                    'primary_keys': primary_keys,
                    'foreign_keys': foreign_keys,
                    'indexes': indexes,
                    'row_count': statistics.get('row_count', 0),
                    'total_size': statistics.get('total_size', 'Unknown')
                }
            }
        
        except Exception as e:
            raise Exception(f"Failed to import table schema: {e}")
        finally:
            self.disconnect()
    
    def _get_columns(self, conn, table_name: str, schema: str) -> List[Dict]:
        """Get column information from information_schema."""
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                col_description(
                    (quote_ident(%s) || '.' || quote_ident(%s))::regclass::oid,
                    ordinal_position
                ) as column_comment
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        
        cursor.execute(query, (schema, table_name, schema, table_name))
        columns = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in columns]
    
    def _get_primary_keys(self, conn, table_name: str, schema: str) -> List[str]:
        """Get primary key columns."""
        cursor = conn.cursor()
        
        query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
        """
        
        cursor.execute(query, (f"{schema}.{table_name}",))
        pks = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        return pks
    
    def _get_foreign_keys(self, conn, table_name: str, schema: str) -> Dict[str, str]:
        """Get foreign key relationships."""
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
        """
        
        cursor.execute(query, (schema, table_name))
        fks = cursor.fetchall()
        cursor.close()
        
        return {
            row['column_name']: f"{row['foreign_table_name']}.{row['foreign_column_name']}"
            for row in fks
        }
    
    def _get_indexes(self, conn, table_name: str, schema: str) -> List[str]:
        """Get table indexes."""
        cursor = conn.cursor()
        
        query = """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = %s AND tablename = %s
        """
        
        cursor.execute(query, (schema, table_name))
        indexes = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        return indexes
    
    def _get_table_comment(self, conn, table_name: str, schema: str) -> Optional[str]:
        """Get table comment/description."""
        cursor = conn.cursor()
        
        query = """
            SELECT obj_description(%s::regclass)
        """
        
        cursor.execute(query, (f"{schema}.{table_name}",))
        result = cursor.fetchone()
        cursor.close()
        
        return result[0] if result and result[0] else None
    
    def get_table_statistics(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """
        Get table statistics including row count and size.
        
        Args:
            table_name: Name of the table
            schema: Database schema name
            
        Returns:
            Dictionary with statistics
        """
        try:
            conn = self.connect()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as row_count FROM {schema}.{table_name}")
            row_count = cursor.fetchone()['row_count']
            
            # Get table size
            query = """
                SELECT pg_size_pretty(pg_total_relation_size(%s)) as total_size
            """
            cursor.execute(query, (f"{schema}.{table_name}",))
            size_result = cursor.fetchone()
            
            cursor.close()
            
            return {
                'row_count': row_count,
                'total_size': size_result['total_size'] if size_result else 'Unknown'
            }
        
        except Exception as e:
            return {
                'row_count': 0,
                'total_size': 'Unknown',
                'error': str(e)
            }
    
    def _is_pii_field(self, field_name: str) -> bool:
        """Detect if field name suggests PII data."""
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in self.PII_KEYWORDS)
    
    def _map_type(self, pg_type: str) -> str:
        """Map PostgreSQL type to generic type."""
        pg_type_lower = pg_type.lower()
        return self.TYPE_MAPPING.get(pg_type_lower, 'string')
