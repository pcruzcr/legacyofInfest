#!/usr/bin/env python3
"""Fix inventory.py load method completely."""
import re

with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find load method
load_start = content.find('    def load(self) -> None:')
if load_start == -1:
    load_start = content.find('def load(self) -> None:')

# Find end of load method
class_start = content.find('class Inventory:')
class_end = content.find('\nclass ', content.find('class Inventory:') + 1)
if class_end == -1:
    class_end = len(content)

class_content = content[content.find('class Inventory:'):content.find('\nclass ', content.find('class Inventory:') + 1) if content.find('\nclass ', content.find('class Inventory:') + 1) != -1 else len(content)]

load_start_in_class = class_content.find('    def load(self) -> None:')
if load_start == -1:
    load_start = class_content.find('def load(self) -> None:')

load_end = class_content.find('\n    def ', class_content.find('def load(self)') + 1)
if load_end == -1:
    load_end = len(class_content)

load_method = class_content[load_start_in_class:load_end]

# New load method
new_load = '''    def load(self) -> None:
        _migrar_inventario()
        try:
            raw = _INVENTORY_PATH.read_bytes()
            data = orjson.loads(raw)
            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}
            # AUD-609 -- un fichero viejo sin la clave deja 0; uno editado a
            # mano con basura también, que es mejor que un multiplicador
            # roto. No se aceptan negativos: el prestigio sólo se gana.
            try:
                self.prestigio = max(0, int(data.get("prestigio", 0)))
            except (TypeError, ValueError):
                self.prestigio = 0
            self._equipped = {
                slot: item_id
                for slot, item_id in data.get("equipped", {}).items()
                if (defn := _ITEM_DEFS.get(item_id)) is not None
                and defn.slot == slot
                and defn.slot != "skill"
                and self._items.get(item_id, 0) > 0
            }
        except FileNotFoundError:
            logger.debug("inventory: sin fichero previo; se empieza de cero")
            self._items = {}
            self._equipped = {}
        except (ValueError, TypeError):
            logger.warning(
                "inventory: %s ilegible; se empieza de cero",
                _INVENTORY_PATH, exc_info=True,
            )
            self._items = {}
            self._equipped = {}

'''

# Replace in content
with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

load_start = content.find('    def load(self) -> None:')
if load_start == -1:
    load_start = content.find('def load(self) -> None:')

class_start = content.find('class Inventory:')
class_end = content.find('\nclass ', content.find('class Inventory:') + 1)
if class_end == -1:
    class_end = len(content)

class_content = content[content.find('class Inventory:'):content.find('\nclass ', content.find('class Inventory:') + 1) if content.find('\nclass ', content.find('class Inventory:') + 1) != -1 else len(content)]

load_start_in_class = class_content.find('    def load(self) -> None:')
if load_start == -1:
    load_start = class_content.find('def load(self) -> None:')

load_end = class_content.find('\n    def ', class_content.find('def load(self)') + 1)
if load_end == -1:
    load_end = len(class_content)

load_method = class_content[load_start_in_class:load_end]

new_load = '''    def load(self) -> None:
        _migrar_inventario()
        try:
            raw = _INVENTORY_PATH.read_bytes()
            data = orjson.loads(raw)
            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}
            # AUD-609 -- un fichero viejo sin la clave deja 0; uno editado a
            # mano con basura también, que es mejor que un multiplicador
            # roto. No se aceptan negativos: el prestigio sólo se gana.
            try:
                self.prestigio = max(0, int(data.get("prestigio", 0)))
            except (TypeError, ValueError):
                self.prestigio = 0
            self._equipped = {
                slot: item_id
                for slot, item_id in data.get("equipped", {}).items()
                if (defn := _ITEM_DEFS.get(item_id)) is not None
                and defn.slot == slot
                and defn.slot != "skill"
                and self._items.get(item_id, 0) > 0
            }
        except FileNotFoundError:
            logger.debug("inventory: sin fichero previo; se empieza de cero")
            self._items = {}
            self._equipped = {}
        except (ValueError, TypeError):
            logger.warning(
                "inventory: %s ilegible; se empieza de cero",
                _INVENTORY_PATH, exc_info=True,
            )
            self._items = {}
            self._equipped = {}

'''

# Replace in content
with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

load_start = content.find('    def load(self) -> None:')
if load_start == -1:
    load_start = content.find('def load(self) -> None:')

class_start = content.find('class Inventory:')
class_end = content.find('\nclass ', content.find('class Inventory:') + 1)
if class_end == -1:
    class_end = len(content)

class_content = content[content.find('class Inventory:'):content.find('\nclass ', content.find('class Inventory:') + 1) if content.find('\nclass ', content.find('class Inventory:') + 1) != -1 else len(content)]

load_start_in_class = class_content.find('    def load(self) -> None:')
if load_start == -1:
    load_start = class_content.find('def load(self) -> None:')

load_end = class_content.find('\n    def ', class_content.find('def load(self)') + 1)
if load_end == -1:
    load_end = len(class_content)

load_method = class_content[load_start_in_class:load_end]

new_load = '''    def load(self) -> None:
        _migrar_inventario()
        try:
            raw = _INVENTORY_PATH.read_bytes()
            data = orjson.loads(raw)
            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}
            # AUD-609 -- un fichero viejo sin la clave deja 0; uno editado a
            # mano con basura también, que es mejor que un multiplicador
            # roto. No se aceptan negativos: el prestigio sólo se gana.
            try:
                self.prestigio = max(0, int(data.get("prestigio", 0)))
            except (TypeError, ValueError):
                self.prestigio = 0
            self._equipped = {
                slot: item_id
                for slot, item_id in data.get("equipped", {}).items()
                if (defn := _ITEM_DEFS.get(item_id)) is not None
                and defn.slot == slot
                and defn.slot != "skill"
                and self._items.get(item_id, 0) > 0
            }
        except FileNotFoundError:
            logger.debug("inventory: sin fichero previo; se empieza de cero")
            self._items = {}
            self._equipped = {}
        except (ValueError, TypeError):
            logger.warning(
                "inventory: %s ilegible; se empieza de cero",
                _INVENTORY_PATH, exc_info=True,
            )
            self._items = {}
            self._equipped = {}

'''

# Replace in content
with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find load method
load_start = content.find('    def load(self) -> None:')
if load_start == -1:
    load_start = content.find('def load(self) -> None:')

# Find end of load method
class_start = content.find('class Inventory:')
class_end = content.find('\nclass ', content.find('class Inventory:') + 1)
if class_end == -1:
    class_end = len(content)

class_content = content[content.find('class Inventory:'):content.find('\nclass ', content.find('class Inventory:') + 1) if content.find('\nclass ', content.find('class Inventory:') + 1) != -1 else len(content)]

load_start_in_class = class_content.find('    def load(self) -> None:')
if load_start == -1:
    load_start = class_content.find('def load(self) -> None:')

load_end = class_content.find('\n    def ', class_content.find('def load(self)') + 1)
if load_end == -1:
    load_end = len(class_content)

# Replace
new_content = content[:load_start] + new_load + content[load_start + len(load_method):]

with open('src/engine/core/inventory.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed inventory.py load method")
PYEOF
.venv\Scripts\python.exe fix_inventory_final.py