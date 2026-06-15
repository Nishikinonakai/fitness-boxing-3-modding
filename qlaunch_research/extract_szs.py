#!/usr/bin/env python3
"""Minimal Yaz0 decompress + SARC extract (pure python). For inspecting qlaunch szs."""
import sys, struct, os

def yaz0_decompress(data: bytes) -> bytes:
    assert data[:4] == b"Yaz0", "not Yaz0"
    dec_size = struct.unpack(">I", data[4:8])[0]
    src = 16
    out = bytearray()
    while len(out) < dec_size and src < len(data):
        flag = data[src]; src += 1
        for bit in range(8):
            if len(out) >= dec_size: break
            if flag & (0x80 >> bit):
                out.append(data[src]); src += 1
            else:
                b1 = data[src]; b2 = data[src+1]; src += 2
                dist = ((b1 & 0x0F) << 8 | b2) + 1
                count = b1 >> 4
                if count == 0:
                    count = data[src] + 0x12; src += 1
                else:
                    count += 2
                start = len(out) - dist
                for i in range(count):
                    out.append(out[start + i])
    return bytes(out)

def sarc_extract(data: bytes):
    assert data[:4] == b"SARC", "not SARC"
    bom = data[6:8]
    endian = ">" if bom == b"\xFE\xFF" else "<"
    data_offset = struct.unpack(endian + "I", data[12:16])[0]
    # SFAT
    assert data[0x14:0x18] == b"SFAT"
    node_count = struct.unpack(endian + "H", data[0x1A:0x1C])[0]
    nodes = []
    p = 0x20
    for _ in range(node_count):
        name_hash, name_attr, start, end = struct.unpack(endian + "IIII", data[p:p+16])
        nodes.append((name_attr, start, end)); p += 16
    # SFNT
    assert data[p:p+4] == b"SFNT"
    sfnt_strings = p + 8
    files = {}
    for name_attr, start, end in nodes:
        name_off = (name_attr & 0xFFFFFF) * 4
        spos = sfnt_strings + name_off
        epos = data.index(b"\x00", spos)
        name = data[spos:epos].decode("utf-8", "replace")
        files[name] = data[data_offset + start: data_offset + end]
    return files

if __name__ == "__main__":
    src = sys.argv[1]; outdir = sys.argv[2]
    raw = open(src, "rb").read()
    if raw[:4] == b"Yaz0":
        raw = yaz0_decompress(raw)
        print("decompressed to", len(raw), "bytes")
    files = sarc_extract(raw)
    os.makedirs(outdir, exist_ok=True)
    for name, content in sorted(files.items()):
        outp = os.path.join(outdir, name.replace("/", "_"))
        open(outp, "wb").write(content)
        print(f"  {name}  ({len(content)} bytes)")
    print(f"\nTotal {len(files)} files extracted to {outdir}")
