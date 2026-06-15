#!/usr/bin/env python3
"""Parse a BFLYT: list panes (type, name, flags, position) and part1(prt1) panes which embed sub-layouts.
Reference: BFLYT format. Pane common header after section magic+size:
  pan1/pic1/txt1/wnd1/bnd1/prt1 share base: flags(1) origin(1) alpha(1) paneMagFlags(1) name(24 bytes, padded)
  userdata(8) then translation(3 floats x,y,z) rotation(3) scale(2) size w,h(2 floats).
"""
import sys, struct

def parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"FLYT", f"not FLYT: {d[:4]}"
    bom = d[4:6]
    en = "<" if bom == b"\xFF\xFE" else ">"
    # header: magic(4) bom(2) headersize(2) version(4) filesize(4) numsections(2) pad(2)
    num_sections = struct.unpack(en+"H", d[0x0E:0x10])[0]
    p = struct.unpack(en+"H", d[6:8])[0]  # header size = offset to first section
    panes = []
    depth = 0
    order = 0
    while p < len(d):
        magic = d[p:p+4]
        if len(magic) < 4: break
        size = struct.unpack(en+"I", d[p+4:p+8])[0]
        if size == 0: break
        if magic in (b"pan1", b"pic1", b"txt1", b"wnd1", b"bnd1", b"prt1"):
            base = p + 8
            flags = d[base]
            visible = bool(flags & 0x01)
            origin = d[base+1]
            alpha = d[base+2]
            name = d[base+4:base+4+24].split(b"\x00")[0].decode("latin1")
            # after name(24) + userdata(8) => translation
            tp = base + 4 + 24 + 8
            tx, ty, tz = struct.unpack(en+"fff", d[tp:tp+12])
            sp = tp + 12 + 12  # skip rotation(3 floats)
            sx, sy = struct.unpack(en+"ff", d[sp:sp+8])
            wp = sp + 8
            w, h = struct.unpack(en+"ff", d[wp:wp+8])
            panes.append({
                "magic": magic.decode(), "name": name, "visible": visible,
                "x": round(tx,2), "y": round(ty,2), "w": round(w,2), "h": round(h,2),
                "sx": round(sx,3), "sy": round(sy,3), "depth": depth, "order": order
            })
            order += 1
        elif magic == b"pas1":
            depth += 1
        elif magic == b"pae1":
            depth -= 1
        p += size
    return panes

if __name__ == "__main__":
    panes = parse(sys.argv[1])
    print(f"{'depth':<6}{'type':<6}{'name':<28}{'vis':<5}{'x':>10}{'y':>10}{'w':>9}{'h':>9}{'sx':>7}{'sy':>7}")
    for pn in panes:
        ind = "  "*pn["depth"]
        print(f"{pn['depth']:<6}{pn['magic']:<6}{ind+pn['name']:<28}{str(pn['visible']):<5}{pn['x']:>10}{pn['y']:>10}{pn['w']:>9}{pn['h']:>9}{pn['sx']:>7}{pn['sy']:>7}")
