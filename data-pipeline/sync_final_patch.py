#!/usr/bin/env python3
# data-pipeline/sync_final_patch.py
# This script patches sync_final.py to add missing imports

import fileinput
import sys

# Read the current file
with open('data-pipeline/sync_final.py', 'r') as f:
    lines = f.readlines()

# Find where to insert the new imports (after existing imports but before class definitions)
insert_position = 0
for i, line in enumerate(lines):
    if line.startswith('from airtable_sync_fixed import'):
        insert_position = i + 1
        break

# Add the missing imports
new_imports = [
    "from datetime import datetime\n",
    "import logging\n",
    "\n",
    "# Configure logging for synchronization operations\n",
    "logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')\n",
    "logger = logging.getLogger(__name__)\n",
    "\n"
]

# Insert the new imports
for import_line in reversed(new_imports):
    lines.insert(insert_position, import_line)

# Write the patched file back
with open('data-pipeline/sync_final.py', 'w') as f:
    f.writelines(lines)

print("Successfully patched sync_final.py with missing imports:")
print("- Added: from datetime import datetime")
print("- Added: import logging")
print("- Added: logger configuration")
print("\nThe file is now ready for synchronization.")
