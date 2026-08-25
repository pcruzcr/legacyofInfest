with open("src/engine/core/i18n.py", "rb") as f:
    raw = f.read()

idx = raw.find(b"ui.inventory_title")
if idx >= 0:
    context = raw[max(0, idx-60):idx+80]
    with open("byte_check.txt", "wb") as f:
        f.write(b"Found at byte offset: " + str(idx).encode() + b"\n")
        f.write(b"Context: " + context + b"\n")
    print("Written to byte_check.txt")
else:
    print("NOT FOUND")