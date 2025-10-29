#!/usr/bin/env python3
# data-pipeline/generate_postgresql_ddl.py
# Generates complete PostgreSQL DDL from parsed AirTable schema
# This creates production-ready SQL with proper constraints, indexes, and relationships

import json
import re
from datetime import datetime
from typing import Dict, List, Set

class PostgreSQLGenerator:
    """
    This generator transforms the parsed AirTable schema into PostgreSQL DDL commands.
    
    The transformation process involves several important architectural decisions:
    1. How to handle AirTable's flexible schema in PostgreSQL's strict typing
    2. How to represent many-to-many relationships using junction tables
    3. How to maintain referential integrity while allowing for data migration
    4. How to optimize for both read and write performance
    
    Think of this as translating between two different database philosophies:
    AirTable's user-friendly, flexible approach versus PostgreSQL's strict, 
    performance-oriented structure.
    """
    
    def __init__(self, schema_file: str):
        with open(schema_file, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)
        
        # Track which tables we've seen to handle relationships properly
        self.processed_tables = set()
        self.junction_tables = []
        
    def generate_ddl(self) -> str:
        """
        Main method that orchestrates the DDL generation process.
        
        The generation follows a specific order to avoid dependency issues:
        1. Create the database and schema
        2. Create lookup/reference tables first (like Commodities)
        3. Create main tables without foreign keys
        4. Add foreign key constraints after all tables exist
        5. Create junction tables for many-to-many relationships
        6. Add indexes for performance optimization
        
        This order ensures that all referenced tables exist before we create
        constraints, preventing errors during database creation.
        """
        ddl_parts = []
        
        # Add header with metadata
        ddl_parts.append(self._generate_header())
        
        # Create schema if needed
        ddl_parts.append(self._generate_schema_setup())
        
        # First, create all main tables without foreign key constraints
        # This prevents circular dependency issues
        for table_name, table_info in self.schema['tables'].items():
            ddl_parts.append(self._generate_table(table_name, table_info, include_fks=False))
            self.processed_tables.add(table_name)
        
        # Now add foreign key constraints as ALTER statements
        ddl_parts.append("\n-- Adding Foreign Key Constraints")
        ddl_parts.append("-- These are added separately to avoid circular dependencies\n")
        for table_name, table_info in self.schema['tables'].items():
            fk_statements = self._generate_foreign_keys(table_name, table_info)
            if fk_statements:
                ddl_parts.extend(fk_statements)
        
        # Create junction tables for many-to-many relationships
        if self.junction_tables:
            ddl_parts.append("\n-- Junction Tables for Many-to-Many Relationships")
            ddl_parts.append("-- These tables handle the relationships between entities\n")
            for junction_sql in self.junction_tables:
                ddl_parts.append(junction_sql)
        
        # Add indexes for performance
        ddl_parts.append(self._generate_indexes())
        
        # Add helpful comments and utility views
        ddl_parts.append(self._generate_utility_views())
        
        return '\n'.join(ddl_parts)
    
    def _generate_header(self) -> str:
        """
        Creates a detailed header comment explaining the database structure.
        
        Good documentation at the database level helps future developers
        understand not just what the structure is, but why it was designed
        this way and how it maps back to the original AirTable system.
        """
        return f"""-- PostgreSQL DDL for AirTable Base: {self.schema['base_id']}
-- Generated: {datetime.now().isoformat()}
-- Source: AirTable API Documentation Parser v2
--
-- This database schema replicates the structure of your AirTable base
-- with the following considerations:
-- 1. AirTable record IDs are preserved in 'airtable_record_id' columns
-- 2. Relationships are maintained using foreign keys and junction tables
-- 3. All tables include created_at and updated_at timestamps
-- 4. Indexes are created on foreign key columns for query performance
--
-- Tables included: {len(self.schema['tables'])} tables
-- Total fields: {sum(t['field_count'] for t in self.schema['tables'].values())} fields
-- Relationships: {sum(1 for t in self.schema['tables'].values() for f in t['fields'].values() if f.get('is_relationship'))} relationships

-- ============================================================"""
    
    def _generate_schema_setup(self) -> str:
        """
        Generates initial database setup commands.
        
        This includes creating the schema (namespace) and setting up
        any database-wide configurations. Using a schema helps organize
        the database and avoid naming conflicts with other applications.
        """
        return """
-- Create schema for better organization
CREATE SCHEMA IF NOT EXISTS airtable_sync;

-- Set search path to include our schema
SET search_path TO airtable_sync, public;

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- For generating UUIDs
CREATE EXTENSION IF NOT EXISTS "btree_gist";  -- For exclusion constraints
"""
    
    def _sanitize_name(self, name: str) -> str:
        """
        Converts AirTable names to PostgreSQL-safe identifiers.
        
        PostgreSQL has strict rules about identifiers:
        - No spaces (we replace with underscores)
        - No parentheses or special characters
        - Should be lowercase for consistency
        - Can't start with numbers
        
        This method ensures all our table and column names are valid.
        """
        # Convert to lowercase and replace problematic characters
        safe = name.lower()
        safe = safe.replace(' ', '_')
        safe = safe.replace('(', '')
        safe = safe.replace(')', '')
        safe = safe.replace('-', '_')
        safe = safe.replace('.', '_')
        safe = safe.replace('%', 'pct')
        safe = safe.replace('/', '_')
        safe = safe.replace(':', '')
        safe = safe.replace(',', '')
        
        # Remove any remaining non-alphanumeric characters except underscore
        safe = re.sub(r'[^a-z0-9_]', '', safe)
        
        # Ensure it doesn't start with a number
        if safe and safe[0].isdigit():
            safe = 'n_' + safe
        
        # PostgreSQL has a 63 character limit for identifiers
        if len(safe) > 63:
            safe = safe[:60] + '_tr'  # tr for "truncated"
        
        return safe
    
    def _generate_table(self, table_name: str, table_info: Dict, include_fks: bool = False) -> str:
        """
        Generates CREATE TABLE statement for a single table.
        
        This method creates the main structure of each table, including:
        - A surrogate primary key (id) for PostgreSQL
        - The original AirTable record ID for reference
        - All data fields with appropriate types
        - Timestamp fields for tracking changes
        - Check constraints for data validation where appropriate
        
        The include_fks parameter controls whether foreign key constraints
        are included inline (which can cause dependency issues) or added
        separately later (which is safer).
        """
        safe_table_name = self._sanitize_name(table_name)
        
        sql = f"\n-- Table: {table_name}"
        if table_info.get('id'):
            sql += f" (AirTable ID: {table_info['id']})"
        sql += f"\nCREATE TABLE IF NOT EXISTS {safe_table_name} (\n"
        
        # Standard fields every table should have
        sql += "    -- Primary key and AirTable reference\n"
        sql += "    id SERIAL PRIMARY KEY,\n"
        sql += "    airtable_record_id VARCHAR(20) UNIQUE,\n"
        sql += "    \n    -- Data fields\n"
        
        # Add all fields from the schema
        field_lines = []
        for field_name, field_info in table_info['fields'].items():
            safe_field_name = self._sanitize_name(field_name)
            postgres_type = field_info.get('postgres_type', 'TEXT')
            
            # Skip array relationship fields (they'll be junction tables)
            if postgres_type == 'INTEGER[]':
                continue
            
            # For single relationships, just use INTEGER (foreign key)
            if field_info.get('is_relationship') and postgres_type == 'INTEGER':
                field_line = f"    {safe_field_name} INTEGER"
                # Add comment to indicate this is a foreign key
                field_line += f"  -- FK to {field_name}"
            else:
                field_line = f"    {safe_field_name} {postgres_type}"
                
            field_lines.append(field_line)
        
        sql += ',\n'.join(field_lines)
        
        # Add timestamp fields
        sql += ",\n    \n    -- Metadata fields\n"
        sql += "    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,\n"
        sql += "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,\n"
        sql += "    sync_status VARCHAR(20) DEFAULT 'pending',\n"
        sql += "    last_airtable_modified TIMESTAMP WITH TIME ZONE\n"
        sql += ");\n"
        
        # Add table comment
        sql += f"\nCOMMENT ON TABLE {safe_table_name} IS '{table_name} data synchronized from AirTable';\n"
        
        return sql
    
    def _generate_foreign_keys(self, table_name: str, table_info: Dict) -> List[str]:
        """
        Generates ALTER TABLE statements to add foreign key constraints.
        
        Foreign keys are crucial for maintaining referential integrity,
        ensuring that relationships between tables remain consistent.
        We add these as separate ALTER statements to avoid circular
        dependency issues during table creation.
        
        For many-to-many relationships (INTEGER[] fields), we create
        junction tables instead of foreign keys.
        """
        safe_table_name = self._sanitize_name(table_name)
        statements = []
        
        for field_name, field_info in table_info['fields'].items():
            if not field_info.get('is_relationship'):
                continue
            
            safe_field_name = self._sanitize_name(field_name)
            postgres_type = field_info.get('postgres_type', 'TEXT')
            
            if postgres_type == 'INTEGER[]':
                # Create junction table for many-to-many relationship
                junction_table_sql = self._create_junction_table(
                    table_name, field_name, field_info
                )
                if junction_table_sql:
                    self.junction_tables.append(junction_table_sql)
            
            elif postgres_type == 'INTEGER':
                # Single foreign key relationship
                referenced_table = self._infer_referenced_table(field_name)
                if referenced_table:
                    safe_referenced_table = self._sanitize_name(referenced_table)
                    constraint_name = f"fk_{safe_table_name}_{safe_field_name}"
                    
                    # Truncate constraint name if it's too long
                    if len(constraint_name) > 63:
                        constraint_name = constraint_name[:60] + '_fk'
                    
                    statements.append(
                        f"ALTER TABLE {safe_table_name} "
                        f"ADD CONSTRAINT {constraint_name} "
                        f"FOREIGN KEY ({safe_field_name}) "
                        f"REFERENCES {safe_referenced_table}(id) "
                        f"ON DELETE SET NULL;"
                    )
        
        return statements
    
    def _create_junction_table(self, source_table: str, field_name: str, 
                               field_info: Dict) -> str:
        """
        Creates a junction table for many-to-many relationships.
        
        In AirTable, you can link multiple records easily, but in PostgreSQL,
        many-to-many relationships require an intermediate junction table.
        This table contains foreign keys to both related tables and possibly
        additional metadata about the relationship itself.
        
        For example, if Contracts links to multiple Shipments, we create
        a contracts_shipments junction table with contract_id and shipment_id.
        """
        safe_source_table = self._sanitize_name(source_table)
        safe_field_name = self._sanitize_name(field_name)
        
        # Infer the target table from the field name
        target_table = self._infer_referenced_table(field_name)
        if not target_table:
            return ""
        
        safe_target_table = self._sanitize_name(target_table)
        
        # Create junction table name
        junction_table_name = f"{safe_source_table}_{safe_field_name}"
        if len(junction_table_name) > 63:
            # Shorten the name if it's too long
            junction_table_name = f"{safe_source_table[:25]}_{safe_field_name[:25]}_jn"
        
        sql = f"\nCREATE TABLE IF NOT EXISTS {junction_table_name} (\n"
        sql += f"    {safe_source_table}_id INTEGER NOT NULL REFERENCES {safe_source_table}(id) ON DELETE CASCADE,\n"
        sql += f"    {safe_target_table}_id INTEGER NOT NULL REFERENCES {safe_target_table}(id) ON DELETE CASCADE,\n"
        sql += "    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,\n"
        sql += f"    PRIMARY KEY ({safe_source_table}_id, {safe_target_table}_id)\n"
        sql += ");\n"
        sql += f"\nCOMMENT ON TABLE {junction_table_name} IS 'Junction table for {source_table}.{field_name} relationship';\n"
        
        return sql
    
    def _infer_referenced_table(self, field_name: str) -> str:
        """
        Infers which table a relationship field references based on the field name.
        
        This method uses naming patterns to determine relationships. For example,
        a field named "Customer" likely references the "Customers" table.
        This is a heuristic approach that works well with consistent naming.
        """
        field_lower = field_name.lower()
        
        # Direct mappings based on field names we've seen
        mappings = {
            'customer': 'Customers',
            'khách hàng': 'Customers',  # Vietnamese for customer
            'commodity type': 'Commodities',
            'commodity': 'Commodities',
            'contract number': 'Contracts (Hợp Đồng)',
            'contract': 'Contracts (Hợp Đồng)',
            'related contract': 'Contracts (Hợp Đồng)',
            'shipment': 'Shipments',
            'related shipment': 'Shipments',
            'related shipments': 'Shipments',
            'inventory movement': 'Inventory Movements',
            'inventory movements': 'Inventory Movements',
            'related inventory movements': 'Inventory Movements',
            'finished goods': 'Finished Goods',
            'price list': 'Price Lists',
            'price lists': 'Price Lists',
            'contracts (hợp đồng) - 2': 'Contracts (Hợp Đồng) - 2'
        }
        
        # Check for exact matches first
        if field_lower in mappings:
            return mappings[field_lower]
        
        # Check for partial matches
        for key, value in mappings.items():
            if key in field_lower:
                return value
        
        # Check if the field name matches any table name
        for table_name in self.schema['tables'].keys():
            if field_lower == table_name.lower():
                return table_name
            # Check plural/singular variations
            if field_lower + 's' == table_name.lower():
                return table_name
            if field_lower == table_name.lower() + 's':
                return table_name
        
        return None
    
    def _generate_indexes(self) -> str:
        """
        Generates indexes for optimizing query performance.
        
        Indexes are crucial for database performance. They work like the index
        in a book - instead of reading every page to find a topic, you can
        jump directly to the right page. We create indexes on:
        - Foreign key columns (for JOIN operations)
        - Commonly searched fields (like dates and names)
        - The AirTable record ID (for synchronization)
        
        The trade-off is that indexes slow down write operations slightly
        but dramatically speed up read operations.
        """
        sql = "\n-- Indexes for Query Performance\n"
        sql += "-- These indexes optimize common query patterns\n\n"
        
        for table_name, table_info in self.schema['tables'].items():
            safe_table_name = self._sanitize_name(table_name)
            
            # Index on AirTable record ID for sync operations
            sql += f"CREATE INDEX idx_{safe_table_name}_airtable_id "
            sql += f"ON {safe_table_name}(airtable_record_id);\n"
            
            # Index on updated_at for incremental sync
            sql += f"CREATE INDEX idx_{safe_table_name}_updated "
            sql += f"ON {safe_table_name}(updated_at);\n"
            
            # Index on foreign key columns
            for field_name, field_info in table_info['fields'].items():
                if field_info.get('is_relationship') and field_info.get('postgres_type') == 'INTEGER':
                    safe_field_name = self._sanitize_name(field_name)
                    sql += f"CREATE INDEX idx_{safe_table_name}_{safe_field_name} "
                    sql += f"ON {safe_table_name}({safe_field_name});\n"
            
            sql += "\n"
        
        return sql
    
    def _generate_utility_views(self) -> str:
        """
        Creates helpful views for common queries.
        
        Views are like saved queries that act like virtual tables.
        They simplify complex queries and provide a consistent interface
        for accessing data. These utility views help with:
        - Monitoring synchronization status
        - Identifying data quality issues
        - Providing business-friendly data access
        """
        sql = "\n-- Utility Views for Data Management\n\n"
        
        # Sync status overview
        sql += "CREATE OR REPLACE VIEW v_sync_status AS\n"
        sql += "SELECT \n"
        sql += "    'contracts' as table_name,\n"
        sql += "    COUNT(*) as total_records,\n"
        sql += "    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,\n"
        sql += "    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,\n"
        sql += "    MAX(updated_at) as last_update\n"
        sql += "FROM contracts_hp_ng\n"
        
        for table_name in list(self.schema['tables'].keys())[1:]:
            safe_table_name = self._sanitize_name(table_name)
            sql += "UNION ALL\n"
            sql += "SELECT \n"
            sql += f"    '{safe_table_name}' as table_name,\n"
            sql += "    COUNT(*) as total_records,\n"
            sql += "    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,\n"
            sql += "    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,\n"
            sql += "    MAX(updated_at) as last_update\n"
            sql += f"FROM {safe_table_name}\n"
        
        sql += ";\n\n"
        sql += "COMMENT ON VIEW v_sync_status IS 'Overview of data synchronization status across all tables';\n"
        
        return sql
    
    def save_ddl(self, output_file: str = 'schema/postgresql_ddl.sql'):
        """
        Saves the generated DDL to a file.
        
        This method generates the complete DDL and saves it to a SQL file
        that can be executed directly in PostgreSQL to create the database schema.
        """
        ddl = self.generate_ddl()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ddl)
        
        print(f"PostgreSQL DDL saved to: {output_file}")
        
        # Count what we generated
        table_count = len(self.schema['tables'])
        junction_count = len(self.junction_tables)
        total_tables = table_count + junction_count
        
        print(f"\nGenerated SQL for:")
        print(f"  - {table_count} main tables")
        print(f"  - {junction_count} junction tables")
        print(f"  - {total_tables} tables total")
        print(f"\nTo create the database, run:")
        print(f"  psql -U your_username -d your_database -f {output_file}")


def main():
    """
    Main function that generates PostgreSQL DDL from the parsed schema.
    """
    print("PostgreSQL DDL Generator")
    print("="*70)
    
    generator = PostgreSQLGenerator('schema/complete_parsed_schema.json')
    generator.save_ddl()
    
    print("\nDDL generation complete!")
    print("Review the generated SQL and adjust any data types if needed.")
    print("Then create your PostgreSQL database using the generated script.")


if __name__ == "__main__":
    main()
