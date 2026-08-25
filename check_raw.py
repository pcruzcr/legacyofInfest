import re
from pathlib import Path

# Read the exact bytes
with open("src/engine/core/i18n.py", "rb") as f:
    raw = f.read()

# Find the ui.inventory_title bytes
idx = raw.find(b'ui.inventory_title')
if idx >= 0:
    print(f"Found at byte offset: {idx}")
    # Show context
    start = max(0, idx - 50)
    end = min(len(raw), idx + 100)
    print(f"Context: {raw[start:end]}")
else:
    print("NOT FOUND in raw bytes!")

# Also check the text version
with open("src/engine/core/i18n.py", "r", encoding="utf-8") as f:
    text = f.read()
    
# Check if the pattern matches in the full text
import re
patron = re.compile(r'"((?:[^"\\]|\\.)*)"')
matches = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto))
for m in matches:
    val = m.group(1)
    if 'inventory' in val:
        print(f"Found in text: {val!r}")