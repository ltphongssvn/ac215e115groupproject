#!/usr/bin/env python3
# data-pipeline/improved_doc_parser.py
# Enhanced parser for AirTable API documentation with correct multi-line field handling

import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ImprovedAirTableDocParser:
    """
    This improved parser correctly handles the multi-line structure of field definitions
    in the AirTable API documentation. Each field spans multiple lines:
    1. Field name concatenated with field ID
    2. AirTable type (like Date, Text, Number, etc.)
    3. Technical type description (like "string (ISO 8601 formatted date)")
    4. Additional description or example values
    
    Understanding this structure is crucial for accurate schema extraction.
    """
    
    def __init__(self, doc_file_path: str):
        self.doc_file_path = doc_file_path
        self.schema = {
            'base_id': 'appmeTyHLozoqighD',
            'parsed_at': datetime.now().isoformat(),
            'source': 'api_documentation_v2',
            'tables': {}
        }
        
    def parse_documentation(self) -> Dict:
        """
        Parses the entire documentation file using improved field extraction logic.
        
        The parsing strategy here is to find table sections first, then within each
        section, locate the Fields area and parse each field definition that spans
        multiple lines. This approach is more robust than trying to parse everything
        with a single regular expression.
        """
        print(f"Parsing documentation from: {self.doc_file_path}")
        
        with open(self.doc_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into lines for easier processing
        lines = content.split('\n')
        
        # Find all table sections
        table_sections = self._find_table_sections(content)
        
        for table_name, start_idx, end_idx in table_sections:
            print(f"\nProcessing table: {table_name}")
            
            # Extract the lines for this table section
            table_lines = lines[start_idx:end_idx]
            table_content = '\n'.join(table_lines)
            
            # Extract table ID
            table_id = self._extract_table_id(table_content, table_name)
            
            # Extract fields with improved parsing
            fields = self._extract_fields_improved(table_lines)
            
            if fields:
                self.schema['tables'][table_name] = {
                    'id': table_id,
                    'name': table_name,
                    'fields': fields,
                    'field_count': len(fields)
                }
                print(f"  Found {len(fields)} fields with correct types")
        
        return self.schema
    
    def _find_table_sections(self, content: str) -> List[Tuple[str, int, int]]:
        """
        Finds all table sections in the documentation and returns their boundaries.
        
        This method identifies where each table's documentation begins and ends,
        which allows us to process each table independently. Think of this as
        creating a table of contents that tells us exactly where to find each
        table's information in the document.
        """
        lines = content.split('\n')
        sections = []
        
        # Pattern to identify table headers
        table_pattern = re.compile(r'^(.+?)\s+[Tt]able$')
        
        for i, line in enumerate(lines):
            match = table_pattern.match(line.strip())
            if match:
                table_name = match.group(1).strip()
                
                # Skip navigation/menu items
                if table_name.lower() in ['introduction', 'metadata', 'rate limits', 
                                         'authentication', 'fields', 'list records']:
                    continue
                
                sections.append((table_name, i))
        
        # Convert to (name, start_idx, end_idx) format
        result = []
        for i, (name, start) in enumerate(sections):
            if i + 1 < len(sections):
                end = sections[i + 1][1]
            else:
                end = len(lines)
            result.append((name, start, end))
        
        return result
    
    def _extract_table_id(self, content: str, table_name: str) -> str:
        """
        Extracts the table ID from the table section content.
        
        The documentation typically contains text like:
        "The id for [Table Name] is tblXXXXXXXXXXXX."
        
        We search for this pattern and extract the table ID.
        """
        # Try various patterns that might appear in the documentation
        patterns = [
            r'[Tt]he id for .+? is (tbl[a-zA-Z0-9]+)',
            r'table id[:\s]+([tbl][a-zA-Z0-9]+)',
            r'(tbl[a-zA-Z0-9]{14,})'  # Just look for something that looks like a table ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # If we can't find it, return the ones we know from previous discovery
        known_ids = {
            "Contracts (Hợp Đồng)": "tbl7sHbwOCOTjL2MC",
            "Contracts (Hợp Đồng) - 2": "tbllz4cazITSwnXIo",
            "Customers": "tblDUfIlNy07Z0hiL",
            "Shipments": "tblSj7JcxYYfs6Dcl",
            "Inventory Movements": "tblhb3Vxhi6Yt0BDw",
            "Finished Goods": "tblNY26FnHswHRcWS"
        }
        
        return known_ids.get(table_name, f"tbl_unknown_{table_name.replace(' ', '_')}")
    
    def _extract_fields_improved(self, table_lines: List[str]) -> Dict:
        """
        Improved field extraction that correctly handles multi-line field definitions.
        
        Each field in the documentation follows this pattern:
        Line 1: FieldNamefldXXXXXXXXXXXX (field name concatenated with field ID)
        Line 2: Type (like Date, Text, Number, Currency, etc.)
        Line 3: Technical description (like "string (ISO 8601 formatted date)")
        Line 4+: Additional description or examples
        
        This method carefully parses each field definition to extract all components.
        """
        fields = {}
        
        # Find where the Fields section starts
        fields_start_idx = None
        for i, line in enumerate(table_lines):
            if line.strip() == 'Fields':
                fields_start_idx = i + 1
                break
        
        if fields_start_idx is None:
            return fields
        
        # Find where Fields section ends (usually at "List records" or end of table)
        fields_end_idx = len(table_lines)
        for i in range(fields_start_idx, len(table_lines)):
            if 'List records' in table_lines[i] or 'Retrieve a record' in table_lines[i]:
                fields_end_idx = i
                break
        
        # Process field definitions in the Fields section
        i = fields_start_idx
        while i < fields_end_idx:
            line = table_lines[i].strip()
            
            # Look for lines containing field IDs (format: fldXXXXXXXXXXXX)
            field_id_match = re.search(r'(fld[a-zA-Z0-9]{14,})', line)
            if field_id_match:
                field_id = field_id_match.group(1)
                
                # Extract field name (everything before the field ID)
                field_id_pos = line.find(field_id)
                field_name = line[:field_id_pos].strip()
                
                # Sometimes there's text after the field ID on the same line
                remaining_text = line[field_id_pos + len(field_id):].strip()
                
                # Look at the next few lines for type information
                airtable_type = ""
                technical_type = ""
                
                if i + 1 < fields_end_idx:
                    next_line = table_lines[i + 1].strip()
                    # If the remaining text from the first line looks like a type, use it
                    if remaining_text and remaining_text[0].isupper():
                        airtable_type = remaining_text
                    # Otherwise, the type should be on the next line
                    elif next_line and not next_line.startswith('fld'):
                        airtable_type = next_line
                
                # Look for technical type description (usually line 3)
                if i + 2 < fields_end_idx:
                    tech_line = table_lines[i + 2].strip()
                    if '(' in tech_line or 'array' in tech_line.lower():
                        technical_type = tech_line
                
                # Determine PostgreSQL type based on what we found
                postgres_type, is_relationship = self._determine_postgres_type(
                    airtable_type, technical_type, table_lines[i:min(i+5, fields_end_idx)]
                )
                
                if field_name:  # Only add if we successfully extracted a field name
                    fields[field_name] = {
                        'name': field_name,
                        'field_id': field_id,
                        'airtable_type': airtable_type,
                        'technical_type': technical_type,
                        'postgres_type': postgres_type,
                        'is_relationship': is_relationship
                    }
            
            i += 1
        
        return fields
    
    def _determine_postgres_type(self, airtable_type: str, technical_type: str, 
                                context_lines: List[str]) -> Tuple[str, bool]:
        """
        Determines the PostgreSQL type based on AirTable type information.
        
        This method now has access to both the simple type name (like "Date" or "Text")
        and the technical description (like "string (ISO 8601 formatted date)"),
        allowing for much more accurate type mapping.
        """
        # Combine all context for analysis
        full_context = ' '.join([airtable_type, technical_type] + context_lines).lower()
        
        # Check for relationship fields first
        if 'link to another record' in full_context or 'linked records' in full_context:
            if 'array of record ids' in full_context:
                return ('INTEGER[]', True)
            else:
                return ('INTEGER', True)
        
        # Now map based on the AirTable type
        type_lower = airtable_type.lower()
        
        # Date types
        if 'date' in type_lower:
            if 'datetime' in full_context or 'timestamp' in full_context:
                return ('TIMESTAMP', False)
            else:
                return ('DATE', False)
        
        # Numeric types
        elif 'number' in type_lower:
            if 'currency' in full_context:
                return ('DECIMAL(15,2)', False)
            elif 'percent' in full_context or '(%)' in ' '.join(context_lines):
                return ('DECIMAL(5,3)', False)
            elif 'decimal' in full_context:
                return ('DECIMAL(15,4)', False)
            else:
                return ('INTEGER', False)
        
        # Currency type
        elif 'currency' in type_lower:
            return ('DECIMAL(15,2)', False)
        
        # Text types
        elif 'text' in type_lower:
            if 'long text' in full_context or 'multiple lines' in full_context:
                return ('TEXT', False)
            else:
                return ('VARCHAR(255)', False)
        
        # Boolean
        elif 'checkbox' in type_lower:
            return ('BOOLEAN', False)
        
        # Other specific types
        elif 'email' in type_lower:
            return ('VARCHAR(254)', False)
        elif 'phone' in type_lower:
            return ('VARCHAR(50)', False)
        elif 'url' in type_lower:
            return ('VARCHAR(2048)', False)
        elif 'select' in type_lower:
            if 'multiple' in full_context:
                return ('TEXT[]', False)
            else:
                return ('VARCHAR(100)', False)
        
        # Default fallback
        else:
            return ('TEXT', False)
    
    def save_parsed_schema(self):
        """
        Saves the parsed schema and generates summary statistics.
        """
        # Save as JSON
        json_path = 'schema/complete_parsed_schema.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.schema, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print(f"Schema successfully parsed and saved to: {json_path}")
        
        # Calculate statistics
        total_fields = sum(table['field_count'] for table in self.schema['tables'].values())
        total_relationships = sum(
            1 for table in self.schema['tables'].values()
            for field in table['fields'].values()
            if field.get('is_relationship', False)
        )
        
        print(f"Total tables found: {len(self.schema['tables'])}")
        print(f"Total fields found: {total_fields}")
        print(f"Total relationships found: {total_relationships}")
        print('='*70)
        
        # Detailed table summary
        print("\nDetailed Table Summary:")
        print("-" * 70)
        for table_name, table_info in self.schema['tables'].items():
            rel_fields = [f for f in table_info['fields'].values() if f.get('is_relationship', False)]
            print(f"\n{table_name} (ID: {table_info['id']})")
            print(f"  Total fields: {table_info['field_count']}")
            print(f"  Relationship fields: {len(rel_fields)}")
            if rel_fields:
                print(f"  Relationships to: {', '.join([f['name'] for f in rel_fields])}")


def main():
    """
    Main execution function for the improved parser.
    """
    doc_file = "Airtable API for Excel database.txt"
    
    print("Starting Improved AirTable API Documentation Parser")
    print("="*70)
    
    parser = ImprovedAirTableDocParser(doc_file)
    schema = parser.parse_documentation()
    parser.save_parsed_schema()
    
    print("\nParsing complete!")
    print("The extracted schema now contains correct field types and relationships.")
    print("Next step: Generate PostgreSQL DDL from this complete schema.")


if __name__ == "__main__":
    main()
