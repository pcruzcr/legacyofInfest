import struct

# Write a minimal 32x32 RGBA PNG (all transparent)
width, height = 32, 32

def chunk(name: bytes, data: bytes) -> bytes:
    c = name + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

import zlib

signature = b"\x89PNG\r\n\x1a\n"
ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
raw = b"\x00" + b"\x00" * (width * 4)  # filter byte + transparent pixels
compressed = zlib.compress(raw)
png = signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")

with open("assets/tileset_stage0.png", "wb") as f:
    f.write(png)
print("wrote assets/tileset_stage0.png")