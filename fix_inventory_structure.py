#!/usr/bin/env python3
"""Fix inventory.py structure: move _ITEM_DEFS before Inventory class, fix load() try/except."""
import re

with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the _ITEM_DEFS dictionary and the Inventory class
# The _ITEM_DEFS dict spans from line 62 to ~457
# The Inventory class starts at line 178
# The load method starts at line 413

# Split the content into parts:
# 1. Header (imports, etc.) - lines 1-61
# 2. _ITEM_DEFS dict (lines 62-457)
# 3. Inventory class (line 178 onwards)

# Find the end of _ITEM_DEFS (the closing brace before Inventory class)
# The _ITEM_DEFS dict ends with "}" at line 457 (0-indexed: 456)
# The Inventory class starts at line 178

# Actually, looking at the structure:
# - Lines 1-61: imports, constants, class ItemDef
# - Lines 62-457: _ITEM_DEFS dict
# - Line 178: class Inventory:
# - Line 413: def load(self)
# Line 415: try:
# Lines 416-457: try block body (includes rest of _ITEM_DEFS!)
# Line 458: } (closes _ITEM_DEFS)
# Line 459: except FileNotFoundError: (at module level - WRONG)
# Line 463: except (ValueError, TypeError): (also at module level)

# The fix:
# 1. Move the entire _ITEM_DEFS dict to be before the Inventory class
# 2. Fix the load() method to have proper try/except structure

# Let's read the entire file and reconstruct it
with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the boundaries
# _ITEM_DEFS starts at line 62 (index 61 in 0-based)
# Find the closing brace of _ITEM_DEFS
# It should be the } that closes the dict started at line 62

# Let's find the Inventory class
inventory_class_idx = content.find('class Inventory:')
print(f"Inventory class at index: {inventory_class_idx}")

# Find _ITEM_DEFS start
item_defs_start = content.find('_ITEM_DEFS: dict[str, ItemDef] = {')
print(f"_ITEM_DEFS starts at index: {item_defs_start}")

# Find the end of _ITEM_DEFS - it's the } that closes the dict
# This is tricky because there are nested braces. Let's find the matching }
def find_matching_brace(text, start_idx):
    """Find the index of the matching closing brace for a dict starting at start_idx."""
    brace_count = 0
    in_string = False
    escape = False
    for i in range(start_idx, len(text)):
        c = text[i]
        if not escape and c == '"' and not in_string:
            in_string = True
        elif not escape and c == '"' and in_string:
            in_string = False
        elif not escape and c == '\\':
            escape = True
        else:
            escape = False
        
        if not in_string:
            if c == '{':
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0:
                    return i
    return -1

# Find the start of _ITEM_DEFS dict
item_defs_start = content.find('_ITEM_DEFS: dict[str, ItemDef] = {')
if item_defs_start == -1:
    print("Could not find _ITEM_DEFS start")
else:
    end_idx = find_matching_brace(content, item_defs_start + len('_ITEM_DEFS: dict[str, ItemDef] = {'))
    print(f"_ITEM_DEFS ends at index: {end_idx}")
    print(f"Content at end: {repr(content[end_idx-10:end_idx+10])}")

# Find class Inventory
class_idx = content.find('class Inventory:')
print(f"class Inventory at index: {class_idx}")

# The _ITEM_DEFS should end before class Inventory
# Let's extract the parts and reconstruct

# Extract parts:
# 1. Header (imports, etc.) - everything before _ITEM_DEFS
# 2. _ITEM_DEFS dict
# 3. Inventory class and rest

header_end = content.find('_ITEM_DEFS: dict[str, ItemDef] = {')
if item_defs_start >= 0:
    header = content[:item_defs_start]
    item_defs_dict = content[item_defs_start:class_idx]
    rest = content[class_idx:]
    
    # Now we need to fix the load() method in the Inventory class
    # Find the load method
    load_method_idx = rest.find('def load(self)')
    if load_method_idx >= 0:
        # Find the try/except structure in load()
        # The issue is that the try block includes the rest of _ITEM_DEFS
        # and the except clauses are at module level
        
        # We need to restructure so that:
        # 1. _ITEM_DEFS is completely defined before the class
        # 2. The load() method has proper try/except
        
        # For now, let's just fix the syntax error by properly closing the try/except
        # The issue is that the try block starts at line 415 (in load method)
        # but the except clauses are at module level
        
        # Let's rewrite the load method properly
        print("Need to restructure the file...")
        print("Current structure is too complex for simple string replacement")
        print("Need to do a more careful rewrite")