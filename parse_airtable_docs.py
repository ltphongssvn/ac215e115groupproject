#!/usr/bin/env python3
# data-pipeline/parse_airtable_docs.py
# Parses AirTable API documentation to extract complete schema information
# This approach bypasses Meta API limitations by using the already-generated documentation

import re
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime

class AirTableDocParser:
    """
    Parses AirTable's API documentation to extract complete schema information.
    
    The API documentation contains all field definitions, types, and relationships
    that AirTable has already analyzed for us. Rather than trying to discover this
    through the API (which has limitations), we're extracting it from documentation
    that AirTable itself generated. This is like reading a technical manual instead
    of reverse-engineering a machine - much more efficient and complete.
    """
    
    def __init__(self, doc_file_path: str):
        """
        Initialize the parser with the path to the API documentation file.
        
        Args:
            doc_file_path: Path to the AirTable API documentation text file
        """
        self.doc_file_path = doc_file_path
        self.schema = {
            'base_id': 'appmeTyHLozoqighD',
            'parsed_at': datetime.now().isoformat(),
            'source': 'api_documentation',
            'tables': {}
        }
        
    def parse_documentation(self) -> Dict:
        """
        Main parsing method that processes the entire documentation file.
        
        The documentation follows a consistent structure where each table section
        starts with the table name followed by "table" or "Table", then contains
        a Fields section listing all fields with their types and descriptions.
        We'll use regular expressions to extract this structured information.
        """
        print(f"Parsing documentation from: {self.doc_file_path}")
        
        with open(self.doc_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all table sections in the documentation
        # Pattern matches lines like "Contracts (Hợp Đồng) Table" or "Customers table"
        table_pattern = r'([^\n]+?)\s+[Tt]able\s*\n'
        table_matches = re.finditer(table_pattern, content)
        
        for match in table_matches:
            table_name = match.group(1).strip()
            
            # Skip generic headings that aren't actual table names
            if table_name.lower() in ['introduction', 'metadata', 'rate limits', 'authentication']:
                continue
            
            print(f"\nProcessing table: {table_name}")
            
            # Extract the section for this table
            start_pos = match.end()
            # Find the next table section or end of file
            next_table = re.search(r'\n[^\n]+?\s+[Tt]able\s*\n', content[start_pos:])
            if next_table:
                end_pos = start_pos + next_table.start()
            else:
                end_pos = len(content)
            
            table_section = content[start_pos:end_pos]
            
            # Extract table ID
            table_id = self._extract_table_id(table_section, table_name)
            
            # Extract fields from this table's section
            fields = self._extract_fields(table_section)
            
            if fields:  # Only add tables where we found fields
                self.schema['tables'][table_name] = {
                    'id': table_id,
                    'name': table_name,
                    'fields': fields,
                    'field_count': len(fields)
                }
                print(f"  Found {len(fields)} fields")
        
        return self.schema
    
    def _extract_table_id(self, section: str, table_name: str) -> str:
        """
        Extracts the table ID from the documentation section.
        
        The documentation typically contains a line like:
        "The id for [Table Name] is tblXXXXXXXXXXXX."
        """
        # Pattern to match table ID
        id_pattern = r'[Tt]he id for [^.]+? is (tbl[a-zA-Z0-9]+)'
        match = re.search(id_pattern, section)
        if match:
            return match.group(1)
        
        # If not found, generate a placeholder
        print(f"  Warning: Could not find table ID for {table_name}")
        return f"tbl_unknown_{table_name.replace(' ', '_')}"
    
    def _extract_fields(self, section: str) -> Dict:
        """
        Extracts field information from a table's documentation section.
        
        The Fields section contains a structured list where each field has:
        - Field Name
        - Field ID (like fldXXXXXXXXXXXX)
        - Type (Text, Number, Date, Link to another record, etc.)
        - Description
        
        We need to parse this carefully to maintain the relationship information.
        """
        fields = {}
        
        # Find the Fields section
        fields_start = section.find('Fields\n')
        if fields_start == -1:
            return fields
        
        # Extract content after "Fields" heading
        fields_section = section[fields_start:]
        
        # Pattern to match field definitions
        # This captures: FieldName[fieldID]Type
        # The pattern is complex because field names can contain special characters
        field_pattern = r'([^\n]+?)(?:fld[a-zA-Z0-9]+)?([A-Z][a-z]+(?:\s+[a-z]+)*)\n'
        
        # Alternative pattern that's more specific
        # Matches lines that start with a field name and contain a field ID
        detailed_pattern = r'^(.+?)(fld[a-zA-Z0-9]+)(.+?)$'
        
        # Split the section into lines and process each
        lines = fields_section.split('\n')
        current_field = None
        current_type = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check if this line contains a field ID (indicates a field definition)
            if 'fld' in line and re.search(r'fld[a-zA-Z0-9]{14,}', line):
                # Extract field name (everything before the field ID)
                field_id_match = re.search(r'(fld[a-zA-Z0-9]+)', line)
                if field_id_match:
                    field_id = field_id_match.group(1)
                    field_name_end = line.find(field_id)
                    field_name = line[:field_name_end].strip()
                    
                    # Extract type (look at the next line or remaining part)
                    type_info = line[field_name_end + len(field_id):].strip()
                    
                    # Determine PostgreSQL type based on AirTable type
                    postgres_type, is_relationship = self._determine_postgres_type(type_info, lines[i:i+5])
                    
                    fields[field_name] = {
                        'name': field_name,
                        'field_id': field_id,
                        'airtable_type': type_info,
                        'postgres_type': postgres_type,
                        'is_relationship': is_relationship
                    }
        
        return fields
    
    def _determine_postgres_type(self, type_info: str, context_lines: List[str]) -> Tuple[str, bool]:
        """
        Determines the appropriate PostgreSQL type based on AirTable type information.
        
        Returns a tuple of (postgres_type, is_relationship)
        
        This method examines both the type string and surrounding context to make
        the best determination of what PostgreSQL type to use.
        """
        # Join context lines to look for additional type hints
        context = ' '.join(context_lines).lower()
        
        # Check for relationship fields
        if 'link to another record' in context or 'linked records' in context:
            # Check if it's array of links (many-to-many)
            if 'array of record ids' in context:
                return ('INTEGER[]', True)
            else:
                return ('INTEGER', True)
        
        # Map AirTable types to PostgreSQL
        type_lower = type_info.lower()
        
        if 'text' in type_lower:
            if 'long text' in context or 'multiple lines' in context:
                return ('TEXT', False)
            else:
                return ('VARCHAR(255)', False)
        
        elif 'number' in type_lower:
            if 'decimal' in context or 'currency' in context:
                return ('DECIMAL(15,2)', False)
            elif 'percent' in context:
                return ('DECIMAL(5,4)', False)
            else:
                return ('INTEGER', False)
        
        elif 'currency' in type_lower:
            return ('DECIMAL(15,2)', False)
        
        elif 'date' in type_lower:
            if 'datetime' in context or 'timestamp' in context:
                return ('TIMESTAMP', False)
            else:
                return ('DATE', False)
        
        elif 'checkbox' in type_lower:
            return ('BOOLEAN', False)
        
        elif 'email' in type_lower:
            return ('VARCHAR(254)', False)
        
        elif 'phone' in type_lower:
            return ('VARCHAR(50)', False)
        
        elif 'url' in type_lower:
            return ('VARCHAR(2048)', False)
        
        elif 'select' in type_lower:
            if 'multiple' in context:
                return ('TEXT[]', False)
            else:
                return ('VARCHAR(100)', False)
        
        else:
            # Default fallback
            return ('TEXT', False)
    
    def save_parsed_schema(self):
        """
        Saves the parsed schema to JSON and generates SQL DDL.
        """
        # Save as JSON
        json_path = 'schema/parsed_airtable_schema.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.schema, f, indent=2, ensure_ascii=False)
        print(f"\n{'='*60}")
        print(f"Schema parsed and saved to: {json_path}")
        
        # Print statistics
        total_fields = sum(table['field_count'] for table in self.schema['tables'].values())
        total_relationships = sum(
            1 for table in self.schema['tables'].values() 
            for field in table['fields'].values() 
            if field.get('is_relationship', False)
        )
        
        print(f"Total tables found: {len(self.schema['tables'])}")
        print(f"Total fields found: {total_fields}")
        print(f"Total relationships found: {total_relationships}")
        print('='*60)
        
        # Print table summary
        print("\nTable Summary:")
        for table_name, table_info in self.schema['tables'].items():
            rel_count = sum(1 for f in table_info['fields'].values() if f.get('is_relationship', False))
            print(f"  {table_name}: {table_info['field_count']} fields, {rel_count} relationships")


def main():
    """
    Main execution function that parses the AirTable API documentation.
    """
    doc_file = "Airtable API for Excel database.txt"
    
    print("Starting AirTable API Documentation Parser")
    print("="*60)
    
    parser = AirTableDocParser(doc_file)
    schema = parser.parse_documentation()
    parser.save_parsed_schema()
    
    print("\nParsing complete! Next steps:")
    print("1. Review the parsed schema in schema/parsed_airtable_schema.json")
    print("2. Use this schema to generate PostgreSQL DDL")
    print("3. Build the data synchronization pipeline")


if __name__ == "__main__":
    main()
