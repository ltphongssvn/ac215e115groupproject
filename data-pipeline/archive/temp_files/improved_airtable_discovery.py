#!/usr/bin/env python3
# data-pipeline/improved_airtable_discovery.py
# Improved AirTable Schema Discovery - Samples more records to discover all fields
# This approach compensates for AirTable's sparse data model and Meta API limitations

import os
import json
import requests
from typing import Dict, Set, Any
from datetime import datetime

class ImprovedAirTableDiscovery:
    """
    This class implements a more thorough discovery process by sampling
    multiple records from each table and merging the discovered fields.
    Think of this like archaeological excavation - we dig in multiple spots
    to get a complete picture of what's buried beneath.
    """
    
    def __init__(self, base_id: str, api_key: str):
        self.base_id = base_id
        self.api_key = api_key
        self.base_url = f"https://api.airtable.com/v0/{base_id}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Known tables from documentation - we cannot discover these automatically
        # without Meta API access, so we maintain this list manually
        self.known_tables = [
            ("tbl7sHbwOCOTjL2MC", "Contracts (Hợp Đồng)"),
            ("tbllz4cazITSwnXIo", "Contracts (Hợp Đồng) - 2"),
            ("tblDUfIlNy07Z0hiL", "Customers"),
            ("tblSj7JcxYYfs6Dcl", "Shipments"),
            ("tblhb3Vxhi6Yt0BDw", "Inventory Movements"),
            ("tblNY26FnHswHRcWS", "Finished Goods")
        ]
    
    def discover_table_schema(self, table_id: str, table_name: str, sample_size: int = 20) -> Dict:
        """
        Discovers schema by sampling multiple records and merging field discoveries.
        
        The key insight here is that AirTable's sparse data model means we need
        to look at many records to see all possible fields. It's like trying to
        understand all the different types of books in a library - you can't just
        look at one shelf, you need to sample from many different sections.
        
        Args:
            table_id: AirTable's internal table identifier
            table_name: Human-readable table name
            sample_size: Number of records to sample (default 20)
        
        Returns:
            Dictionary containing discovered fields and their inferred types
        """
        print(f"  Discovering {table_name} by sampling {sample_size} records...")
        
        discovered_fields = {}
        records_examined = 0
        
        try:
            # Fetch multiple records to increase field discovery coverage
            response = requests.get(
                f"{self.base_url}/{table_id}",
                headers=self.headers,
                params={"maxRecords": sample_size}
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                # Examine each record and merge field discoveries
                for record in records:
                    records_examined += 1
                    fields = record.get('fields', {})
                    
                    for field_name, field_value in fields.items():
                        # If we haven't seen this field before, analyze its type
                        if field_name not in discovered_fields:
                            discovered_fields[field_name] = {
                                'name': field_name,
                                'postgres_type': self._infer_type_from_value(field_value),
                                'sample_value': str(field_value)[:100],  # Store sample for debugging
                                'occurrences': 1
                            }
                        else:
                            # Track how often we see each field
                            discovered_fields[field_name]['occurrences'] += 1
                            
                            # Refine type inference with additional samples
                            current_type = discovered_fields[field_name]['postgres_type']
                            new_type = self._infer_type_from_value(field_value)
                            discovered_fields[field_name]['postgres_type'] = self._merge_type_inference(
                                current_type, new_type
                            )
                
                print(f"    Examined {records_examined} records, found {len(discovered_fields)} fields")
                
            else:
                print(f"    Error: API returned status {response.status_code}")
                
        except Exception as e:
            print(f"    Error discovering table: {e}")
        
        return discovered_fields
    
    def _infer_type_from_value(self, value: Any) -> str:
        """
        Infers PostgreSQL data type from a field value.
        
        This method has been enhanced to better recognize different data patterns,
        particularly for relationship fields and numeric types with varying precision.
        """
        if value is None:
            return 'TEXT'
        elif isinstance(value, bool):
            return 'BOOLEAN'
        elif isinstance(value, int):
            # Check if it's a large number that might be currency
            if abs(value) > 1000000:
                return 'BIGINT'
            return 'INTEGER'
        elif isinstance(value, float):
            # Detect percentage values (typically between 0 and 1)
            if 0 <= value <= 1:
                return 'DECIMAL(5,4)'
            return 'DECIMAL(15,4)'
        elif isinstance(value, list):
            # This is a relationship field (array of record IDs)
            if value and isinstance(value[0], str) and value[0].startswith('rec'):
                return 'INTEGER[]'  # Will be foreign key array
            return 'TEXT[]'
        elif isinstance(value, str):
            # Enhanced string type detection
            if value.startswith('rec'):
                return 'VARCHAR(20)'  # AirTable record ID
            elif '@' in value:
                return 'VARCHAR(254)'  # Email
            elif value.count('-') == 2 and len(value) == 10:
                return 'DATE'
            elif len(value) > 1000:
                return 'TEXT'  # Long text
            elif len(value) > 255:
                return 'VARCHAR(500)'
            else:
                return 'VARCHAR(255)'
        else:
            return 'JSONB'
    
    def _merge_type_inference(self, type1: str, type2: str) -> str:
        """
        Merges two inferred types, choosing the more general one when they differ.
        
        This is important because a field might contain different precision values
        across records. We want to choose a type that can accommodate all values.
        """
        if type1 == type2:
            return type1
        
        # If one is TEXT, use TEXT (most general)
        if 'TEXT' in type1 or 'TEXT' in type2:
            return 'TEXT'
        
        # For VARCHAR fields, use the longer one
        if 'VARCHAR' in type1 and 'VARCHAR' in type2:
            len1 = int(type1.split('(')[1].split(')')[0]) if '(' in type1 else 255
            len2 = int(type2.split('(')[1].split(')')[0]) if '(' in type2 else 255
            return f'VARCHAR({max(len1, len2)})'
        
        # For numeric types, prefer DECIMAL over INTEGER
        if ('DECIMAL' in type1 or 'DECIMAL' in type2) and ('INTEGER' in type1 or 'INTEGER' in type2):
            return 'DECIMAL(15,4)'
        
        # Default to the first type if we can't determine
        return type1
    
    def discover_all_tables(self) -> Dict:
        """
        Discovers schema for all known tables by sampling multiple records from each.
        """
        schema = {
            'base_id': self.base_id,
            'discovered_at': datetime.now().isoformat(),
            'discovery_method': 'improved_sampling',
            'tables': {}
        }
        
        print(f"Starting improved discovery for base {self.base_id}")
        print(f"Will sample up to 20 records per table for better field coverage\n")
        
        for table_id, table_name in self.known_tables:
            fields = self.discover_table_schema(table_id, table_name)
            
            schema['tables'][table_name] = {
                'id': table_id,
                'name': table_name,
                'fields': fields,
                'discovery_stats': {
                    'fields_found': len(fields),
                    'most_common_field': max(fields.items(), 
                                            key=lambda x: x[1].get('occurrences', 0))[0] 
                                            if fields else None
                }
            }
        
        return schema
    
    def save_discovery_results(self, schema: Dict):
        """
        Saves the discovered schema to a JSON file with statistics.
        """
        output_path = 'schema/improved_discovery.json'
        
        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=2)
        
        # Print discovery statistics
        print(f"\n{'='*60}")
        print("Discovery Statistics:")
        print(f"{'='*60}")
        
        total_fields = 0
        for table_name, table_info in schema['tables'].items():
            fields_count = len(table_info['fields'])
            total_fields += fields_count
            print(f"{table_name}: {fields_count} fields discovered")
        
        print(f"\nTotal fields discovered: {total_fields}")
        print(f"Discovery results saved to: {output_path}")


def main():
    """
    Main execution function for improved schema discovery.
    """
    BASE_ID = "appmeTyHLozoqighD"
    API_KEY = os.getenv("AIRTABLE_API_KEY", "")
    
    if not API_KEY:
        print("Error: AIRTABLE_API_KEY environment variable not set")
        return
    
    discoverer = ImprovedAirTableDiscovery(BASE_ID, API_KEY)
    schema = discoverer.discover_all_tables()
    discoverer.save_discovery_results(schema)


if __name__ == "__main__":
    main()
