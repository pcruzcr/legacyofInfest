#!/usr/bin/env python3
"""Fix inventory.py load method completely."""

with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Load method is at lines 412-475 (1-indexed)
# 0-indexed: 411 to 474 (inclusive)
load_start = 411  # 0-indexed
load_end = 475    # inclusive

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

with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Load method is at lines 412-475 (1-indexed)
# 0-indexed: 411 to 475 (inclusive)
load_start = 411
load_end = 475  # inclusive

new_load_lines = [
    '    def load(self) -> None:\n',
    '        _migrar_inventario()\n',
    '        try:\n',
    '            raw = _INVENTORY_PATH.read_bytes()\n',
    '            data = orjson.loads(raw)\n',
    '            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}\n',
    '            # AUD-609 -- un fichero viejo sin la clave deja 0; uno editado a\n',
    '            # mano con basura también, que es mejor que un multiplicador\n',
    '            # roto. No se aceptan negativos: el prestigio sólo se gana.\n',
    '            try:\n',
    '                self.prestigio = max(0, int(data.get("prestigio", 0)))\n',
    '            except (TypeError, ValueError):\n',
    '                self.prestigio = 0\n',
    '            self._equipped = {\n',
    '                slot: item_id\n',
    '            for slot, item_id in data.get("equipped", {}).items()\n',
    '                if (defn := _ITEM_DEFS.get(item_id)) is not None\n',
    '            and defn.slot == slot\n',
    '            and defn.slot != "skill"\n',
    '            and self._items.get(item_id, 0) > 0\n',
    '            }\n',
    '        except FileNotFoundError:\n',
    '            logger.debug("inventory: sin fichero previo; se empieza de cero")\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '        except (ValueError, TypeError):\n',
    '            logger.warning(\n',
    '                "inventory: %s ilegible; se empieza de cero",\n',
    '                _INVENTORY_PATH, exc_info=True,\n',
    '            )\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '\n'
]

# Read all lines
with open('src/engine/core/inventory.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Load method is at lines 412-475 (1-indexed)
# 0-indexed: 411 to 475 (inclusive)
load_start = 411
load_end = 475  # inclusive

# Replace lines 411-475 (0-indexed)
new_lines = lines[:411] + [line + '\n' if not line.endswith('\n') else line for line in [
    '    def load(self) -> None:\n',
    '        _migrar_inventario()\n',
    '        try:\n',
    '            raw = _INVENTORY_PATH.read_bytes()\n',
    '            data = orjson.loads(raw)\n',
    '            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}\n',
    '            # AUD-609 -- un fichero viejo sin la clave deja 0; uno editado a\n',
    '            # mano con basura también, que es mejor que un multiplicador\n',
    '            # roto. No se aceptan negativos: el prestigio sólo se gana.\n',
    '            try:\n',
    '                self.prestigio = max(0, int(data.get("prestigio", 0)))\n',
    '            except (TypeError, ValueError):\n',
    '                self.prestigio = 0\n',
    '            self._equipped = {\n',
    '                slot: item_id\n',
    '            for slot, item_id in data.get("equipped", {}).items()\n',
    '                if (defn := _ITEM_DEFS.get(item_id)) is not None\n',
    '            and defn.slot == slot\n',
    '            and defn.slot != "skill"\n',
    '            and self._items.get(item_id, 0) > 0\n',
    '            }\n',
    '        except FileNotFoundError:\n',
    '            logger.debug("inventory: sin fichero previo; se empieza de cero")\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '        except (ValueError, TypeError):\n',
    '            logger.warning(\n',
    '                "inventory: %s ilegible; se empieza de cero",\n',
    '                _INVENTORY_PATH, exc_info=True,\n',
    '            )\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '\n'
]

new_lines = lines[:411] + [line + '\n' if not line.endswith('\n') else line for line in [
    '    def load(self) -> None:\n',
    '        _migrar_inventario()\n',
    '        try:\n',
    '            raw = _INVENTORY_PATH.read_bytes()\n',
    '            data = orjson.loads(raw)\n',
    '            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}\n',
    '            # AUD-609 -- un fichero viejo sin la clave deja 0; uno editado a\n',
    '            # mano con basura también, que es mejor que un multiplicador\n',
    '            # roto. No se aceptan negativos: el prestigio sólo se gana.\n',
    '            try:\n',
    '                self.prestigio = max(0, int(data.get("prestigio", 0)))\n',
    '            except (TypeError, ValueError):\n',
    '                self.prestigio = 0\n',
    '            self._equipped = {\n',
    '                slot: item_id\n',
    '            for slot, item_id in data.get("equipped", {}).items()\n',
    '                if (defn := _ITEM_DEFS.get(item_id)) is not None\n',
    '            and defn.slot == slot\n',
    '            and defn.slot != "skill"\n',
    '            and self._items.get(item_id, 0) > 0\n',
    '            }\n',
    '        except FileNotFoundError:\n',
    '            logger.debug("inventory: sin fichero previo; se empieza de cero")\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '        except (ValueError, TypeError):\n',
    '            logger.warning(\n',
    '                "inventory: %s ilegible; se empieza de cero",\n',
    '                _INVENTORY_PATH, exc_info=True,\n',
    '            )\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '\n'
]

# Load method is at lines 412-475 (1-indexed)
# 0-indexed: 411 to 475 (inclusive)
load_start = 411
load_end = 475  # inclusive

new_load_lines = [
    '    def load(self) -> None:\n',
    '        _migrar_inventario()\n',
    '        try:\n',
    '            raw = _INVENTORY_PATH.read_bytes()\n',
    '            data = orjson.loads(raw)\n',
    '            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}\n',
    '            # AUD-609 -- un fichero viejo sin la clave deja 0; uno editado a\n',
    '            # mano con basura también, que es mejor que un multiplicador\n',
    '            # roto. No se aceptan negativos: el prestigio sólo se gana.\n',
    '            try:\n',
    '                self.prestigio = max(0, int(data.get("prestigio", 0)))\n',
    '            except (TypeError, ValueError):\n',
    '                self.prestigio = 0\n',
    '            self._equipped = {\n',
    '                slot: item_id\n',
    '            for slot, item_id in data.get("equipped", {}).items()\n',
    '                if (defn := _ITEM_DEFS.get(item_id)) is not None\n',
    '            and defn.slot == slot\n',
    '            and defn.slot != "skill"\n',
    '            and self._items.get(item_id, 0) > 0\n',
    '            }\n',
    '        except FileNotFoundError:\n',
    '            logger.debug("inventory: sin fichero previo; se empieza de cero")\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '        except (ValueError, TypeError):\n',
    '            logger.warning(\n',
    '                "inventory: %s ilegible; se empieza de cero",\n',
    '                _INVENTORY_PATH, exc_info=True,\n',
    '            )\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '\n'
]

new_lines = lines[:411] + [line + '\n' if not line.endswith('\n') else line for line in [
    '    def load(self) -> None:\n',
    '        _migrar_inventario()\n',
    '        try:\n',
    '            raw = _INVENTORY_PATH.read_bytes()\n',
    '            data = orjson.loads(raw)\n',
    '            self._items = {k: v for k, v in data.get("items", {}).items() if k in _ITEM_DEFS}\n',
    '            # AUD-609 -- un fichero viejo sin la clave deja 0; uno editado a\n',
    '            # mano con basura también, que es mejor que un multiplicador\n',
    '            # roto. No se aceptan negativos: el prestigio sólo se gana.\n',
    '            try:\n',
    '                self.prestigio = max(0, int(data.get("prestigio", 0)))\n',
    '            except (TypeError, ValueError):\n',
    '                self.prestigio = 0\n',
    '            self._equipped = {\n',
    '                slot: item_id\n',
    '            for slot, item_id in data.get("equipped", {}).items()\n',
    '                if (defn := _ITEM_DEFS.get(item_id)) is not None\n',
    '            and defn.slot == slot\n',
    '            and defn.slot != "skill"\n',
    '            and self._items.get(item_id, 0) > 0\n',
    '            }\n',
    '        except FileNotFoundError:\n',
    '            logger.debug("inventory: sin fichero previo; se empieza de cero")\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '        except (ValueError, TypeError):\n',
    '            logger.warning(\n',
    '                "inventory: %s ilegible; se empieza de cero",\n',
    '                _INVENTORY_PATH, exc_info=True,\n',
    '            )\n',
    '            self._items = {}\n',
    '            self._equipped = {}\n',
    '\n'
]

load_start = 411
load_end = 475

new_lines = lines[:411] + [line + '\n' if not line.endswith('\n') else line for line in new_load.splitlines(keepends=True)] + lines[475:]

with open('src/engine/core/inventory.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed inventory.py load method")
PYEOF
.venv\Scripts\python.exe fix_inventory_load.py