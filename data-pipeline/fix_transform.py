#!/usr/bin/env python3
# data-pipeline/fix_transform.py
# Fixes the transform_record method to handle both string and dict list items

# Read the airtable_sync.py file
with open('data-pipeline/airtable_sync.py', 'r') as f:
    content = f.read()

# Find and replace the problematic line
old_code = "if isinstance(value, list) and value and value[0].startswith('rec'):"
new_code = """if isinstance(value, list) and value:
                    # Handle both string IDs and dict objects in lists
                    first_item = value[0]
                    if isinstance(first_item, str) and first_item.startswith('rec'):"""

# Additional fix for dict handling
dict_handling = """elif isinstance(first_item, dict) and 'id' in first_item:
                        # Extract IDs from dict objects (linked records with metadata)
                        value = [item.get('id') if isinstance(item, dict) else item for item in value]"""

# Replace in the content
if old_code in content:
    # First replace the condition
    content = content.replace(old_code, new_code)
    
    # Find where to insert the dict handling
    # It should go right after the string handling block
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        new_lines.append(lines[i])
        # Look for the line we just modified
        if "if isinstance(first_item, str) and first_item.startswith('rec'):" in lines[i]:
            # Skip to the next line after the if block (usually the value extraction)
            i += 1
            if i < len(lines):
                new_lines.append(lines[i])
                # Add our elif clause for dict handling
                # Count the indentation of the if statement
                indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                new_lines.append(' ' * indent + "    elif isinstance(first_item, dict) and 'id' in first_item:")
                new_lines.append(' ' * indent + "        # Extract IDs from dict objects (linked records with metadata)")
                new_lines.append(' ' * indent + "        value = [item.get('id') if isinstance(item, dict) else item for item in value]")
        i += 1
    
    content = '\n'.join(new_lines)
    
    # Write the fixed content back
    with open('data-pipeline/airtable_sync.py', 'w') as f:
        f.write(content)
    
    print("Successfully fixed the transform_record method!")
    print("The code now handles both formats of linked records:")
    print("  1. Simple string IDs: ['recXYZ123', 'recABC456']")
    print("  2. Dictionary objects: [{'id': 'recXYZ123', 'name': 'Item Name'}]")
else:
    print("Could not find the exact code to replace.")
    print("The file may have already been modified or has a different format.")
    print("Please check line 195 in airtable_sync.py manually.")

