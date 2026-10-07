"""Rough printed-weight estimate (PLA 1.24 g/cm3).
Model: outer shell (perimeters / top-bottom skins, ~0.75 mm deep) is solid,
the rest is filled at INFILL. Thin parts therefore come out nearly solid."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import connect4 as c4
SHELL, INFILL, RHO = 0.75, 0.15, 1.24
COUNT = {k: int(k.split("_x")[-1]) for k in c4.PARTS}
def estimate():
    rows, tot = [], 0.0
    for name, fn in c4.PARTS.items():
        s = fn().val()
        v, a = s.Volume(), s.Area()
        shell = min(v, a * SHELL)
        g = (shell + INFILL * (v - shell)) / 1000 * RHO
        n = COUNT[name]; tot += g * n
        rows.append((name, v / 1000, g, n, g * n))
    return rows, tot
if __name__ == "__main__":
    rows, tot = estimate()
    for name, v, g, n, gt in rows:
        print(f"{name:16s} solid {v:6.1f} cm3   ~{g:5.1f} g each  x{n:<2d} = {gt:6.1f} g")
    print(f"TOTAL ~{tot:.0f} g  (shell {SHELL} mm, infill {INFILL:.0%})")
