#!/usr/bin/env python3
# data-pipeline/enhanced_schema_builder.py
# Enhanced Schema Builder - Combines discovered schema with known API documentation
# This creates a complete PostgreSQL schema with proper relationships

import json
import os
from datetime import datetime
from typing import Dict, List, Any

class EnhancedSchemaBuilder:
    """
    This class takes the automatically discovered schema and enhances it with
    the complete field list we know from the API documentation. Think of this
    as filling in the gaps in our knowledge - we have a partial map from discovery,
    and we're completing it with information from the documentation.
    """
    
    def __init__(self, discovered_schema_path: str = "schema/airtable_schema.json"):
        """
        Initializes the builder by loading the discovered schema as our foundation.
        We'll build upon what we already discovered rather than starting from scratch.
        """
        with open(discovered_schema_path, 'r') as f:
            self.base_schema = json.load(f)
        
        # This is the complete field mapping from the API documentation
        # I'm defining this based on what we saw in your AirTable API docs
        self.complete_fields = self._define_complete_fields()
        
    def _define_complete_fields(self) -> Dict:
        """
        Defines the complete field structure based on the API documentation.
        This is our "truth source" for what the complete schema should look like.
        
        Notice how each field has specific metadata about its type and purpose.
        This helps us create appropriate PostgreSQL columns with the right constraints.
        """
        return {
            "Contracts (Hợp Đồng)": {
                "Contract Date": ("DATE", False),  # (PostgreSQL type, is_relationship)
                "Contract Number": ("VARCHAR(50)", False),
                "Customer": ("INTEGER", True),  # Foreign key to Customers
                "Quantity (kg)": ("INTEGER", False),
                "Entry Date": ("DATE", False),
                "Voucher Number": ("VARCHAR(50)", False),
                "Commodity Type": ("INTEGER", True),  # Foreign key to Commodities
                "Unit Price": ("DECIMAL(10,2)", False),
                "Transport Cost": ("DECIMAL(10,2)", False),
                "Total Price (incl. Transport)": ("DECIMAL(10,2)", False),
                "Received Quantity": ("INTEGER", False),
                "Quantity Received at DN": ("INTEGER", False),
                "Loss": ("INTEGER", False),
                "Total Amount": ("DECIMAL(15,2)", False),
                "Protein": ("DECIMAL(5,2)", False),
                "Ash": ("DECIMAL(5,2)", False),
                "Fibre": ("DECIMAL(5,2)", False),
                "Fat": ("DECIMAL(5,2)", False),
                "Moisture": ("DECIMAL(5,2)", False),
                "Starch": ("DECIMAL(5,2)", False),
                "Acid Value": ("DECIMAL(5,2)", False),
                "Notes": ("TEXT", False),
                "Related Shipments": ("INTEGER[]", True),
                "Related Inventory Movements": ("INTEGER[]", True),
                "Price Lists": ("INTEGER[]", True)
            },
            "Contracts (Hợp Đồng) - 2": {
                "Contract Date": ("DATE", False),
                "Contract Number": ("VARCHAR(50)", False),
                "Customer": ("INTEGER", True),
                "Quantity (kg)": ("INTEGER", False),
                "Receipt Date": ("VARCHAR(50)", False),  # Keeping as VARCHAR since it might have Excel serial
                "Receipt Number": ("VARCHAR(50)", False),
                "Commodity Type": ("INTEGER", True),
                "Unit Price": ("DECIMAL(10,2)", False),
                "Logistics Cost (VC)": ("INTEGER", False),
                "Total Price (with VC)": ("DECIMAL(10,2)", False),
                "Received Quantity": ("INTEGER", False),
                "Imported Quantity (ĐN)": ("INTEGER", False),
                "Loss": ("INTEGER", False),
                "Total Value": ("DECIMAL(15,2)", False),
                "Protein (%)": ("DECIMAL(5,3)", False),
                "Ash (%)": ("DECIMAL(5,3)", False),
                "Fibre (%)": ("DECIMAL(5,3)", False),
                "Fat (%)": ("DECIMAL(5,3)", False),
                "Moisture (%)": ("DECIMAL(5,3)", False),
                "Starch (%)": ("DECIMAL(5,3)", False),
                "Acid Value (%)": ("DECIMAL(5,3)", False),
                "Notes": ("TEXT", False),
                "Related Inventory Movements": ("INTEGER[]", True)
            },
            "Customers": {
                "Customer Name": ("VARCHAR(255)", False),
                "National ID (CCCD)": ("VARCHAR(20)", False),
                "Address": ("TEXT", False),
                "Contracts": ("INTEGER[]", True),
                "Shipments": ("INTEGER[]", True),
                "Inventory Movements": ("INTEGER[]", True),
                "Finished Goods": ("INTEGER[]", True),
                "Contracts (Hợp Đồng) - 2": ("INTEGER[]", True)
            },
            "Shipments": {
                "Shipment Date": ("DATE", False),
                "Customer": ("INTEGER", True),
                "Contract Number": ("INTEGER", True),
                "Commodity Type": ("INTEGER", True),
                "Vehicle/Container Number": ("VARCHAR(50)", False),
                "Contract Quantity": ("INTEGER", False),
                "Delivered Quantity (kg)": ("INTEGER", False),
                "Arrival Time": ("VARCHAR(50)", False),
                "Unloading Date": ("VARCHAR(50)", False),
                "Inventory Movements": ("INTEGER[]", True),
                "Contracts (Hợp Đồng) - 2": ("INTEGER[]", True)
            },
            "Inventory Movements": {
                "Date": ("DATE", False),
                "Batch/Note": ("VARCHAR(255)", False),
                "Customer": ("INTEGER", True),
                "Vehicle/Container": ("VARCHAR(50)", False),
                "LDH/KH": ("VARCHAR(50)", False),
                "Commodity Type": ("INTEGER", True),
                "Opening Balance (Tons)": ("DECIMAL(10,2)", False),
                "Quantity Received (Tons)": ("DECIMAL(10,2)", False),
                "Internal Transfer Out (Tons)": ("DECIMAL(10,2)", False),
                "Recovered Finished Goods In (Tons)": ("DECIMAL(10,2)", False),
                "Domestic Sales Out (Tons)": ("DECIMAL(10,2)", False),
                "Production Out (Tons)": ("DECIMAL(10,2)", False),
                "Loss 1.3% (from 1/6/2025)": ("DECIMAL(10,2)", False),
                "Raw Material Sales Out (Tons)": ("DECIMAL(10,2)", False),
                "Closing Balance (Tons)": ("DECIMAL(10,2)", False),
                "Fat (%)": ("DECIMAL(5,2)", False),
                "Moisture (%)": ("DECIMAL(5,2)", False),
                "Starch": ("DECIMAL(5,2)", False),
                "Acid Value": ("DECIMAL(5,2)", False),
                "Related Contract": ("INTEGER", True),
                "Related Shipment": ("INTEGER", True),
                "Contracts (Hợp Đồng) - 2": ("INTEGER[]", True)
            },
            "Finished Goods": {
                "Ngày nhập": ("VARCHAR(50)", False),
                "Khách hàng": ("INTEGER", True),
                "LDH": ("VARCHAR(50)", False),
                "Máy": ("VARCHAR(50)", False),
                "Sản xuất tổng giờ": ("INTEGER", False),
                "16h30-19h": ("INTEGER", False),
                "19h-7h": ("INTEGER", False),
                "Mì": ("VARCHAR(50)", False),
                "Số lượng container": ("INTEGER", False),
                "Số lượng theo đầu bao - Trong giờ": ("DECIMAL(10,2)", False),
                "Số lượng theo đầu bao - Ngoài giờ": ("DECIMAL(10,2)", False),
                "Tiền bồi dưỡng BX CONT (50K/20T, 100K/40T)": ("DECIMAL(10,2)", False),
                "Tiền BX trong giờ (23K)": ("DECIMAL(10,2)", False),
                "Ngoài giờ": ("DECIMAL(10,2)", False),
                "Tổng (ca 1)": ("DECIMAL(10,2)", False),
                "Số lượng container (ca 2)": ("INTEGER", False),
                "Số lượng theo đầu bao - Trong giờ (ca 2)": ("DECIMAL(10,2)", False),
                "Số lượng theo đầu bao - Ngoài giờ (ca 2)": ("DECIMAL(10,2)", False),
                "Tiền bồi dưỡng BX CONT (ca 2)": ("DECIMAL(10,2)", False),
                "Tiền BX trong giờ (ca 2)": ("DECIMAL(10,2)", False),
                "Ngoài giờ (ca 2)": ("DECIMAL(10,2)", False)
            }
        }
        
    def enhance_schema(self) -> Dict:
        """
        Enhances the discovered schema with complete field information.
        This is where we merge what we found with what we know should exist.
        """
        enhanced = self.base_schema.copy()
        
        for table_name, table_info in enhanced['tables'].items():
            if table_name in self.complete_fields:
                # Keep existing discovered fields but add missing ones
                complete_fields = self.complete_fields[table_name]
                
                # Add missing fields
                for field_name, (pg_type, is_relationship) in complete_fields.items():
                    if field_name not in table_info['fields']:
                        table_info['fields'][field_name] = {
                            'name': field_name,
                            'postgres_type': pg_type,
                            'is_relationship': is_relationship,
                            'source': 'documentation'  # Mark that this came from docs
                        }
                    else:
                        # Update existing field with relationship info
                        table_info['fields'][field_name]['is_relationship'] = is_relationship
                
                # Build relationships list
                table_info['relationships'] = []
                for field_name, field_info in table_info['fields'].items():
                    if field_info.get('is_relationship', False):
                        table_info['relationships'].append({
                            'field_name': field_name,
                            'type': 'foreign_key' if not field_info['postgres_type'].endswith('[]') else 'many_to_many'
                        })
        
        enhanced['enhanced_at'] = datetime.now().isoformat()
        return enhanced
    
    def generate_complete_sql(self) -> str:
        """
        Generates comprehensive PostgreSQL DDL with all tables, fields, and relationships.
        This creates a production-ready schema that maintains referential integrity.
        """
        enhanced = self.enhance_schema()
        sql = []
        
        # Header comments explaining the schema
        sql.append("-- Complete PostgreSQL Schema for Rice Market AirTable Database")
        sql.append(f"-- Generated: {datetime.now().isoformat()}")
        sql.append("-- This schema includes both discovered and documented fields")
        sql.append("")
        
        # First, create a commodities lookup table (referenced by many tables)
        sql.append("-- Lookup table for commodity types (referenced by multiple tables)")
        sql.append("CREATE TABLE IF NOT EXISTS commodities (")
        sql.append("    id SERIAL PRIMARY KEY,")
        sql.append("    airtable_id VARCHAR(20) UNIQUE,")
        sql.append("    name VARCHAR(100) NOT NULL,")
        sql.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        sql.append(");")
        sql.append("")
        
        # Create main tables
        for table_name, table_info in enhanced['tables'].items():
            safe_name = self._sanitize_name(table_name)
            
            sql.append(f"-- Table: {table_name}")
            sql.append(f"CREATE TABLE IF NOT EXISTS {safe_name} (")
            sql.append("    id SERIAL PRIMARY KEY,")
            sql.append("    airtable_id VARCHAR(20) UNIQUE,")
            
            # Add all fields
            for field_name, field_info in table_info['fields'].items():
                if not field_info.get('is_relationship', False) or not field_info['postgres_type'].endswith('[]'):
                    safe_field = self._sanitize_name(field_name)
                    pg_type = field_info['postgres_type']
                    
                    # Add foreign key reference for single relationships
                    if field_info.get('is_relationship', False):
                        # Determine the referenced table
                        ref_table = self._get_referenced_table(field_name)
                        if ref_table:
                            sql.append(f"    {safe_field} INTEGER REFERENCES {ref_table}(id),")
                        else:
                            sql.append(f"    {safe_field} {pg_type},")
                    else:
                        sql.append(f"    {safe_field} {pg_type},")
            
            sql.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
            sql.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            sql.append(");")
            sql.append("")
            
            # Create indexes for foreign keys
            for field_name, field_info in table_info['fields'].items():
                if field_info.get('is_relationship', False) and not field_info['postgres_type'].endswith('[]'):
                    safe_field = self._sanitize_name(field_name)
                    sql.append(f"CREATE INDEX idx_{safe_name}_{safe_field} ON {safe_name}({safe_field});")
            sql.append("")
        
        # Create junction tables for many-to-many relationships
        sql.append("-- Junction tables for many-to-many relationships")
        for table_name, table_info in enhanced['tables'].items():
            safe_table = self._sanitize_name(table_name)
            
            for rel in table_info.get('relationships', []):
                if rel['type'] == 'many_to_many':
                    field_name = rel['field_name']
                    safe_field = self._sanitize_name(field_name)
                    
                    # Determine the target table
                    target_table = self._get_referenced_table(field_name)
                    if target_table:
                        junction_name = f"{safe_table}_{safe_field}_junction"
                        
                        sql.append(f"CREATE TABLE IF NOT EXISTS {junction_name} (")
                        sql.append(f"    {safe_table}_id INTEGER REFERENCES {safe_table}(id) ON DELETE CASCADE,")
                        sql.append(f"    {target_table}_id INTEGER REFERENCES {target_table}(id) ON DELETE CASCADE,")
                        sql.append(f"    PRIMARY KEY ({safe_table}_id, {target_table}_id)")
                        sql.append(");")
                        sql.append("")
        
        return '\n'.join(sql)
    
    def _sanitize_name(self, name: str) -> str:
        """
        Converts AirTable field/table names to PostgreSQL-safe identifiers.
        PostgreSQL has strict rules about identifiers - no spaces, parentheses, etc.
        """
        # Remove or replace problematic characters
        safe = name.lower()
        safe = safe.replace(' ', '_')
        safe = safe.replace('(', '')
        safe = safe.replace(')', '')
        safe = safe.replace('-', '_')
        safe = safe.replace('.', '_')
        safe = safe.replace('%', 'pct')
        safe = safe.replace('/', '_')
        
        # Remove any remaining non-alphanumeric characters except underscore
        safe = ''.join(c if c.isalnum() or c == '_' else '' for c in safe)
        
        # Ensure it doesn't start with a number
        if safe and safe[0].isdigit():
            safe = 'n' + safe
        
        return safe
    
    def _get_referenced_table(self, field_name: str) -> str:
        """
        Determines which table a relationship field references based on the field name.
        This is pattern matching based on common naming conventions.
        """
        field_lower = field_name.lower()
        
        if 'customer' in field_lower:
            return 'customers'
        elif 'commodity' in field_lower:
            return 'commodities'
        elif 'shipment' in field_lower:
            return 'shipments'
        elif 'contract' in field_lower and '2' in field_lower:
            return 'contracts_hp_ng_2'
        elif 'contract' in field_lower:
            return 'contracts_hp_ng'
        elif 'inventory' in field_lower:
            return 'inventory_movements'
        elif 'finished' in field_lower:
            return 'finished_goods'
        elif 'price' in field_lower and 'list' in field_lower:
            return 'price_lists'  # Assuming this table exists
        
        return None
    
    def save_enhanced_schema(self):
        """
        Saves the enhanced schema and SQL to files.
        This creates our final, production-ready schema definition.
        """
        # Save enhanced JSON schema
        enhanced = self.enhance_schema()
        with open('schema/enhanced_airtable_schema.json', 'w') as f:
            json.dump(enhanced, f, indent=2)
        print("Enhanced schema saved to schema/enhanced_airtable_schema.json")
        
        # Save complete SQL
        sql = self.generate_complete_sql()
        with open('schema/complete_postgresql_schema.sql', 'w') as f:
            f.write(sql)
        print("Complete SQL schema saved to schema/complete_postgresql_schema.sql")
        
        # Generate statistics
        total_fields = sum(len(t['fields']) for t in enhanced['tables'].values())
        total_relationships = sum(len(t.get('relationships', [])) for t in enhanced['tables'].values())
        
        print(f"\nSchema Statistics:")
        print(f"  Tables: {len(enhanced['tables'])}")
        print(f"  Total Fields: {total_fields}")
        print(f"  Relationships: {total_relationships}")
        print(f"  Foreign Keys: {sum(1 for t in enhanced['tables'].values() for r in t.get('relationships', []) if r['type'] == 'foreign_key')}")
        print(f"  Many-to-Many: {sum(1 for t in enhanced['tables'].values() for r in t.get('relationships', []) if r['type'] == 'many_to_many')}")


def main():
    """
    Main execution function that builds the complete enhanced schema.
    """
    print("Building enhanced schema with complete field definitions...")
    
    builder = EnhancedSchemaBuilder()
    builder.save_enhanced_schema()
    
    print("\nEnhanced schema building complete!")
    print("Next steps:")
    print("  1. Review the generated SQL in schema/complete_postgresql_schema.sql")
    print("  2. Create a PostgreSQL database")
    print("  3. Run the SQL to create the schema")
    print("  4. Build the data synchronization pipeline")


if __name__ == "__main__":
    main()
