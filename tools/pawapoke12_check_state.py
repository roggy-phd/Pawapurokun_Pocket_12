#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
melonDS savestate checker for the PowerPoke 12 third-pitch patch (Stage A … v22). Standard library only.
Usage (PowerShell):  python .\\pawapoke12_check_state.py "PAWAPOKE12_stageA_hooktest.ml1"
"""
import struct, sys

def load(fn):
    d = open(fn, "rb").read()
    if d[:4] != b"MELN": raise SystemExit("not a melonDS savestate")
    off = 0x10; sec = {}
    while off + 16 <= len(d):
        tag = d[off:off + 4]; ln = struct.unpack_from("<I", d, off + 4)[0]
        if ln < 16: break
        sec[tag] = off; off += ln
    g = sec[b"NDSG"] + 16
    console = struct.unpack_from("<I", d, g)[0]
    ram = d[g + 4:g + 4 + 0x400000]                      # DS mode main RAM (4 MB)
    return console, ram

def rd(ram, a, n): o = a & 0x3FFFFF; return ram[o:o + n]

def main(fn):
    console, ram = load(fn)
    print(f"file: {fn}   console type: {console} ({'DS' if console == 0 else 'DSi'})")
    hook = rd(ram, 0x0215F2B4, 4).hex(); cave = rd(ram, 0x021934E8, 20).hex()
    ov10_sig = rd(ram, 0x0216AC9C, 4).hex()
    if ov10_sig != "69e0fdeb":
        print("overlay 10 is NOT resident (not in a baseball game?) -> test not applicable"); return
    if hook == "8bd000ea" and cave == "08109fe5e500a0e30000c1e5f087bde8e80b0c02":
        print("overlay 10 in RAM: Stage A hook PRESENT")
    elif hook == "f087bde8":
        print("Stage A hook: not present (normal for Stage B/C/D builds)")
    else:
        print(f"overlay 10 in RAM: UNKNOWN hook bytes {hook} / cave {cave}")
    h1=rd(ram,0x020EBF38,4).hex(); h2=rd(ram,0x020EC1E0,4).hex(); d=rd(ram,0x02147FB8,8)
    if h1=="e06f01ea" and h2=="496f01eb" and rd(ram,0x0214804E,4)!=b"PKP3":
        print(f"Stage B v1 in RAM: PRESENT  flag={d[0]} saved={d[1]:02X} cat={d[2]} third={d[3]:02X} addr=0x{int.from_bytes(d[4:8],'little'):08X}")
    else:
        print(f"Stage B v1 in RAM: not present" + (" (Stage C hooks present instead)" if (rd(ram,0x0214804E,4)==b"PKP3" and h1=="e06f01ea") else f" (overlay 3 hooks not in RAM: {h1} / {h2})"))
    if rd(ram,0x0214804E,4)==b"PKP3" and rd(ram,0x020EBF38,4).hex()=="e06f01ea":
        d=rd(ram,0x02147FEC,8)
        print(f"Stage C in RAM: PRESENT  swap-flag={d[0]} saved={d[1]:02X} cat={d[2]} addr=0x{int.from_bytes(d[4:8],'little'):08X}")

    if rd(ram,0x02172B64,4).hex()=="a57d00eb":
        v21=rd(ram,0x021723F4,4).hex()=="dd7f00eb"
        g=rd(ram,0x02192368 if v21 else 0x02192390,6)
        print(f"CPU third pitch (D1{' v21: games + auto-pennant' if v21 else ': played games only'}) in RAM: PRESENT  eligible decisions={int.from_bytes(g[0:2],'little')} third picks={int.from_bytes(g[2:4],'little')} last third byte={g[4]:02X} last category={g[5]}")
    else:
        print("CPU third pitch (D1) in RAM: not present (or overlay 10 not loaded)")
    if rd(ram,0x021A7758,4).hex()=="24abffeb":
        g=rd(ram,0x0219256C,4)
        c,f=int.from_bytes(g[0:2],'little'),int.from_bytes(g[2:4],'little')
        print(f"Batter read of third pitches (v22) in RAM: PRESENT  split reads={c} forced misses={f}" + (f" ({f/c:.0%})" if c else ""))
    else:
        print("Batter read of third pitches (v22) in RAM: not present (or overlay 15 not loaded)")
    sel=int.from_bytes(rd(ram,0x020D0E44,4),'little')
    if 0x02000000<=sel<0x02400000: print(f"selected pitch code = {rd(ram,sel+1,1)[0]} (6=slow, c=1st, c+7=2nd of category c), display byte = {rd(ram,sel,1)[0]:02X}")
    print(f"0x020C0BE8 (team0 pitcher0 slot4) = {rd(ram, 0x020C0BE8, 1).hex().upper()}   (E4=SFF Lv7, E5=Changeup Lv7)")
    print(f"0x020C0BF4 (team0 pitcher0 +0x14 flag word) = {rd(ram, 0x020C0BF4, 4).hex(' ')}")
    for t in (0, 1):
        print(f"team {t} in-game pitcher table (spd/?/ctl/sta | 12 pitch slots):")
        for i in range(12):
            a = 0x020C0BE0 + t * 0x210 + i * 0x2C
            e = rd(ram, a, 16)
            print(f"  [{i:2}] {a:08X}  {e[:4].hex(' ')} | {e[4:16].hex(' ')}")

if __name__ == "__main__":
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    for f in sys.argv[1:]: main(f)
