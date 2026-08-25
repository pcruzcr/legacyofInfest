with open("src/engine/core/i18n.py", "rb") as f:
    raw = f.read()

idx = raw.find(b"ui.inventory_title")
with open("byte_check.txt", "wb") as f:
    if idx >= 0:
        f.write(b"Found at byte offset: " + str(idx).encode() + b"\n")
        context = raw[max(0, idx-60):idx+80]
        f.write(b"Context: " + context + b"\n")
    else:
        f.write(b"NOT FOUND")