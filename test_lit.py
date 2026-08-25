import sys
sys.path.insert(0, '.')
from scripts.check_translations import todos_los_literales

lit = todos_los_literales()
print(f'ui.inventory_title in lit: {"ui.inventory_title" in lit}')
print(f'Total literales: {len(lit)}')

# Check if i18n.py literals are included
in_i18n = [l for l in lit if 'inventory' in l]
print(f'Inventory-related literals: {in_i18n}')