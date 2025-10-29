import fileinput
import sys

# Read the file and replace plt.show() with save commands
with open('data-pipeline/market_drivers.py', 'r') as f:
    lines = f.readlines()

# Add matplotlib backend setting after imports
new_lines = []
added_backend = False
for i, line in enumerate(lines):
    if not added_backend and 'import matplotlib.pyplot as plt' in line:
        new_lines.append(line)
        new_lines.append("matplotlib.use('Agg')  # Non-interactive backend\n")
        added_backend = True
    elif 'plt.show()' in line:
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + '# plt.show()  # Disabled for pipeline\n')
        new_lines.append(' ' * indent + 'plt.savefig(PROCESSED_DATA_DIR / f"market_factor_{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}.png", dpi=300)\n')
        new_lines.append(' ' * indent + 'plt.close()\n')
    else:
        new_lines.append(line)

# Write back
with open('data-pipeline/market_drivers.py', 'w') as f:
    f.writelines(new_lines)

print("Fixed market_drivers.py to save charts instead of displaying")
