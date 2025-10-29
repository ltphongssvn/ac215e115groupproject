#!/usr/bin/env python3
# data-pipeline/airtable_schema_discovery.py
# AirTable Schema Discovery Script - Extracts complete database schema from AirTable API
# This script discovers all tables, fields, relationships, and data types programmatically

import os
import json
import requests
from typing import Dict, List, Any
from datetime import datetime

class AirTableSchemaDiscovery:
    """
    Discovers and documents the complete schema of an AirTable base.
    This class follows the principle of API introspection - letting the 
    data source tell us about its structure rather than hardcoding assumptions.
    """
    
    def __init__(self, base_id: str, api_key: str):
        self.base_id = base_id
        self.api_key = api_key
        self.base_url = f"https://api.airtable.com/v0/{base_id}"
        self.meta_url = f"https://api.airtable.com/v0/meta/bases/{base_id}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.schema = {
            "base_id": base_id,
            "discovered_at": datetime.now().isoformat(),
            "tables": {}
        }
    
    def discover_schema(self) -> Dict[str, Any]:
        """
        Main discovery method that orchestrates the schema extraction process.
        Think of this as conducting a survey of the entire database structure.
        """
        print(f"Starting schema discovery for base {self.base_id}...")
        
        # Step 1: Get base metadata including all tables
        # The meta API endpoint provides the complete structure
        try:
            response = requests.get(
                f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables",
                headers=self.headers
            )
            
            if response.status_code == 200:
                tables_data = response.json()
                print(f"Found {len(tables_data.get('tables', []))} tables in the base")
                
                # Process each table's schema
                for table in tables_data.get('tables', []):
                    self._process_table_schema(table)
                    
            else:
                print(f"Warning: Meta API returned status {response.status_code}")
                print("Falling back to manual discovery...")
                self._manual_discovery()
                
        except Exception as e:
            print(f"Error accessing meta API: {e}")
            print("Attempting manual discovery through data API...")
            self._manual_discovery()
        
        return self.schema
    
    def _process_table_schema(self, table_meta: Dict) -> None:
        """
        Processes individual table metadata to extract field definitions.
        This method maps AirTable field types to SQL-compatible types.
        """
        table_id = table_meta.get('id')
        table_name = table_meta.get('name')
        
        print(f"  Processing table: {table_name} ({table_id})")
        
        self.schema['tables'][table_name] = {
            'id': table_id,
            'name': table_name,
            'fields': {},
            'relationships': [],
            'primary_field': table_meta.get('primaryFieldId'),
            'description': table_meta.get('description', '')
        }
        
        # Process each field in the table
        for field in table_meta.get('fields', []):
            field_info = self._analyze_field(field)
            self.schema['tables'][table_name]['fields'][field['name']] = field_info
            
            # Track relationships for foreign key creation
            if field['type'] == 'multipleRecordLinks':
                self.schema['tables'][table_name]['relationships'].append({
                    'field_name': field['name'],
                    'field_id': field['id'],
                    'linked_table_id': field.get('options', {}).get('linkedTableId'),
                    'relationship_type': 'many-to-many'  # AirTable uses junction tables internally
                })
    
    def _analyze_field(self, field: Dict) -> Dict:
        """
        Analyzes individual field metadata to determine PostgreSQL data type.
        This is where we map AirTable's type system to PostgreSQL's type system.
        """
        field_type = field.get('type')
        field_options = field.get('options', {})
        
        # Map AirTable types to PostgreSQL types
        # This mapping is crucial for maintaining data integrity during migration
        type_mapping = {
            'singleLineText': 'VARCHAR(255)',
            'multilineText': 'TEXT',
            'richText': 'TEXT',
            'number': self._determine_number_type(field_options),
            'percent': 'DECIMAL(5,4)',  # Stores percentages as decimals
            'currency': 'DECIMAL(15,2)',
            'singleSelect': 'VARCHAR(100)',
            'multipleSelects': 'TEXT[]',  # PostgreSQL array type
            'date': 'DATE',
            'dateTime': 'TIMESTAMP',
            'checkbox': 'BOOLEAN',
            'url': 'VARCHAR(2048)',
            'email': 'VARCHAR(254)',
            'phoneNumber': 'VARCHAR(50)',
            'multipleRecordLinks': 'INTEGER[]',  # Will be foreign key references
            'multipleLookupValues': 'JSONB',  # Complex type, store as JSON
            'formula': 'TEXT',  # Computed field
            'rollup': 'JSONB',
            'count': 'INTEGER',
            'autoNumber': 'SERIAL',
            'barcode': 'VARCHAR(100)',
            'rating': 'INTEGER',
            'duration': 'INTERVAL'
        }
        
        postgres_type = type_mapping.get(field_type, 'TEXT')
        
        return {
            'id': field.get('id'),
            'name': field.get('name'),
            'airtable_type': field_type,
            'postgres_type': postgres_type,
            'description': field.get('description', ''),
            'options': field_options,
            'is_computed': field_type in ['formula', 'rollup', 'count', 'multipleLookupValues'],
            'is_required': field_options.get('required', False)
        }
    
    def _determine_number_type(self, options: Dict) -> str:
        """
        Determines the appropriate PostgreSQL numeric type based on field options.
        Precision matters in financial systems, so we carefully choose types.
        """
        precision = options.get('precision', 0)
        negative = options.get('negative', True)
        
        if precision == 0:
            # Integer type
            return 'INTEGER' if negative else 'INTEGER CHECK (value >= 0)'
        else:
            # Decimal type with specific precision
            return f'DECIMAL(15,{precision})'
    
    def _manual_discovery(self) -> None:
        """
        Fallback method for schema discovery when meta API is unavailable.
        This approach samples actual data to infer the schema structure.
        """
        # List of known tables from the documentation you provided
        known_tables = [
            ("tbl7sHbwOCOTjL2MC", "Contracts (Hợp Đồng)"),
            ("tbllz4cazITSwnXIo", "Contracts (Hợp Đồng) - 2"),
            ("tblDUfIlNy07Z0hiL", "Customers"),
            ("tblSj7JcxYYfs6Dcl", "Shipments"),
            ("tblhb3Vxhi6Yt0BDw", "Inventory Movements"),
            ("tblNY26FnHswHRcWS", "Finished Goods")
        ]
        
        for table_id, table_name in known_tables:
            print(f"  Manually discovering: {table_name}")
            self._discover_table_by_sampling(table_id, table_name)
    
    def _discover_table_by_sampling(self, table_id: str, table_name: str) -> None:
        """
        Discovers table schema by sampling actual records.
        This is less reliable than meta API but works as a fallback.
        """
        try:
            # Fetch a few records to analyze structure
            response = requests.get(
                f"{self.base_url}/{table_id}",
                headers=self.headers,
                params={"maxRecords": 3}
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                if records:
                    # Analyze first record's fields
                    sample_fields = records[0].get('fields', {})
                    
                    self.schema['tables'][table_name] = {
                        'id': table_id,
                        'name': table_name,
                        'fields': {},
                        'relationships': [],
                        'discovered_by': 'sampling'
                    }
                    
                    for field_name, field_value in sample_fields.items():
                        # Infer type from value
                        postgres_type = self._infer_type_from_value(field_value)
                        self.schema['tables'][table_name]['fields'][field_name] = {
                            'name': field_name,
                            'postgres_type': postgres_type,
                            'inferred': True
                        }
                        
        except Exception as e:
            print(f"    Error sampling table {table_name}: {e}")
    
    def _infer_type_from_value(self, value: Any) -> str:
        """
        Infers PostgreSQL data type from actual field values.
        This is our detective work - looking at the evidence to deduce the type.
        """
        if value is None:
            return 'TEXT'  # Default when we can't determine
        elif isinstance(value, bool):
            return 'BOOLEAN'
        elif isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'DECIMAL(15,4)'
        elif isinstance(value, list):
            # Could be array of foreign keys or multi-select
            if value and isinstance(value[0], str) and value[0].startswith('rec'):
                return 'INTEGER[]'  # Foreign key references
            return 'TEXT[]'
        elif isinstance(value, str):
            # Try to detect specific string types
            if value.startswith('rec'):
                return 'VARCHAR(20)'  # AirTable record ID
            elif '@' in value:
                return 'VARCHAR(254)'  # Email
            elif len(value) > 255:
                return 'TEXT'
            elif value.count('-') == 2 and len(value) == 10:
                return 'DATE'  # Date format
            else:
                return 'VARCHAR(255)'
        else:
            return 'JSONB'  # Complex types
    
    def generate_sql_schema(self) -> str:
        """
        Generates PostgreSQL CREATE TABLE statements from discovered schema.
        This is where we translate our discoveries into actionable SQL.
        """
        sql_statements = []
        sql_statements.append("-- PostgreSQL Schema for AirTable Base: " + self.base_id)
        sql_statements.append("-- Generated: " + self.schema['discovered_at'])
        sql_statements.append("")
        
        # Create tables first (without foreign keys)
        for table_name, table_info in self.schema['tables'].items():
            sql = self._generate_create_table(table_name, table_info)
            sql_statements.append(sql)
        
        # Add foreign key constraints separately
        # This two-phase approach prevents circular dependency issues
        for table_name, table_info in self.schema['tables'].items():
            fk_statements = self._generate_foreign_keys(table_name, table_info)
            sql_statements.extend(fk_statements)
        
        return '\n'.join(sql_statements)
    
    def _generate_create_table(self, table_name: str, table_info: Dict) -> str:
        """
        Generates individual CREATE TABLE statement.
        Notice how we sanitize table names for PostgreSQL compatibility.
        """
        # Sanitize table name for PostgreSQL
        safe_table_name = table_name.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
        
        sql = f"CREATE TABLE IF NOT EXISTS {safe_table_name} (\n"
        sql += "    id SERIAL PRIMARY KEY,\n"
        sql += "    airtable_id VARCHAR(20) UNIQUE,\n"  # Preserve original AirTable ID
        sql += "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
        sql += "    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
        
        # Add fields
        for field_name, field_info in table_info['fields'].items():
            if not field_info.get('is_computed', False):  # Skip computed fields initially
                safe_field_name = field_name.replace(' ', '_').replace('(', '').replace(')', '').lower()
                postgres_type = field_info.get('postgres_type', 'TEXT')
                sql += f"    {safe_field_name} {postgres_type},\n"
        
        sql = sql.rstrip(',\n') + "\n);\n"
        return sql
    
    def _generate_foreign_keys(self, table_name: str, table_info: Dict) -> List[str]:
        """
        Generates foreign key constraints for relationships.
        This maintains referential integrity in our PostgreSQL database.
        """
        statements = []
        safe_table_name = table_name.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
        
        for relationship in table_info.get('relationships', []):
            # For many-to-many relationships, we need a junction table
            # This is a key architectural decision for maintaining data relationships
            field_name = relationship['field_name']
            safe_field_name = field_name.replace(' ', '_').replace('(', '').replace(')', '').lower()
            
            junction_table = f"{safe_table_name}_{safe_field_name}_junction"
            
            sql = f"""
-- Junction table for {table_name}.{field_name} relationship
CREATE TABLE IF NOT EXISTS {junction_table} (
    {safe_table_name}_id INTEGER REFERENCES {safe_table_name}(id) ON DELETE CASCADE,
    related_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ({safe_table_name}_id, related_id)
);
"""
            statements.append(sql)
        
        return statements
    
    def save_schema(self, output_dir: str = "data-pipeline/schema") -> None:
        """
        Saves discovered schema to files for documentation and review.
        Good documentation is crucial for maintainability.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save as JSON for programmatic use
        json_path = os.path.join(output_dir, "airtable_schema.json")
        with open(json_path, 'w') as f:
            json.dump(self.schema, f, indent=2)
        print(f"Schema saved to {json_path}")
        
        # Save SQL DDL statements
        sql_path = os.path.join(output_dir, "postgresql_schema.sql")
        with open(sql_path, 'w') as f:
            f.write(self.generate_sql_schema())
        print(f"SQL DDL saved to {sql_path}")
        
        # Generate documentation
        doc_path = os.path.join(output_dir, "schema_documentation.md")
        with open(doc_path, 'w') as f:
            f.write(self._generate_documentation())
        print(f"Documentation saved to {doc_path}")
    
    def _generate_documentation(self) -> str:
        """
        Generates human-readable documentation of the discovered schema.
        This helps team members understand the data model quickly.
        """
        doc = []
        doc.append("# AirTable to PostgreSQL Schema Documentation")
        doc.append(f"\nBase ID: `{self.base_id}`")
        doc.append(f"Discovered: {self.schema['discovered_at']}")
        doc.append(f"\n## Tables ({len(self.schema['tables'])})")
        
        for table_name, table_info in self.schema['tables'].items():
            doc.append(f"\n### {table_name}")
            doc.append(f"- Table ID: `{table_info.get('id', 'Unknown')}`")
            doc.append(f"- Fields: {len(table_info['fields'])}")
            doc.append(f"- Relationships: {len(table_info.get('relationships', []))}")
            
            doc.append("\n#### Fields:")
            for field_name, field_info in table_info['fields'].items():
                airtable_type = field_info.get('airtable_type', 'Unknown')
                postgres_type = field_info.get('postgres_type', 'TEXT')
                doc.append(f"- **{field_name}**: {airtable_type} → {postgres_type}")
        
        return '\n'.join(doc)


def main():
    """
    Main execution function that orchestrates the schema discovery process.
    """
    # These would normally come from environment variables for security
    BASE_ID = "appmeTyHLozoqighD"
    API_KEY = os.getenv("AIRTABLE_API_KEY", "")
    
    if not API_KEY:
        print("Error: AIRTABLE_API_KEY environment variable not set")
        print("Please set it with: export AIRTABLE_API_KEY='your_key_here'")
        return
    
    # Initialize discovery
    discoverer = AirTableSchemaDiscovery(BASE_ID, API_KEY)
    
    # Discover schema
    schema = discoverer.discover_schema()
    
    # Save results
    discoverer.save_schema()
    
    # Print summary
    print(f"\nDiscovery complete!")
    print(f"Found {len(schema['tables'])} tables")
    total_fields = sum(len(t['fields']) for t in schema['tables'].values())
    print(f"Total fields: {total_fields}")
    total_relationships = sum(len(t.get('relationships', [])) for t in schema['tables'].values())
    print(f"Total relationships: {total_relationships}")


if __name__ == "__main__":
    main()
