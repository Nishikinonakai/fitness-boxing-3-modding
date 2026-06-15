import struct, sys

AWB_IN, HCA, AWB_OUT, TARGET = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])

def align_up(x, a): return (x + a - 1) // a * a

data = open(AWB_IN,"rb").read()
assert data[:4]==b"AFS2"
version, offset_size = data[4], data[5]
id_size   = struct.unpack_from("<H", data, 6)[0]
count     = struct.unpack_from("<I", data, 8)[0]
alignment = struct.unpack_from("<H", data, 0x0C)[0]
ofmt = {2:"<H",4:"<I"}[offset_size]
ids_start = 0x10
ofs_start = ids_start + count*id_size
offsets = [struct.unpack_from(ofmt, data, ofs_start + i*offset_size)[0] for i in range(count+1)]
print(f"AFS2 ver={version} off={offset_size} id={id_size} count={count} align={alignment}")

# Real data start = align_up(stored offset); blob pure data = [aligned_start, next_stored_offset)
pure = [data[align_up(offsets[i],alignment):offsets[i+1]] for i in range(count)]
print(f"blob{TARGET} pure: {len(pure[TARGET])}B  (HCA magic {pure[TARGET][:4]!r})")

our = open(HCA,"rb").read()
pure[TARGET] = our
print(f"-> replaced with our HCA {len(our)}B (magic {our[:4]!r})")

# Rebuild body: each blob's data starts at align_up(cursor); stored offset = end of prev data (unaligned)
out = bytearray(data[:offsets[0]])           # header + ids + offset table region (rewritten below)
new_stored = [offsets[0]]
body = bytearray()
for i in range(count):
    start = align_up(new_stored[i], alignment)
    body += b"\x00"*(start - new_stored[i])  # alignment padding
    body += pure[i]
    new_stored.append(start + len(pure[i]))   # end of this blob's data (unaligned)
for i,o in enumerate(new_stored):
    struct.pack_into(ofmt, out, ofs_start + i*offset_size, o)
out += body
open(AWB_OUT,"wb").write(out)
print(f"wrote {AWB_OUT}: {len(out)}B (orig {len(data)}B, delta {len(out)-len(data):+d})")
