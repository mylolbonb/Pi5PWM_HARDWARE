"""Interference + clearance check of the assembled game (all 42 discs loaded)."""
import itertools, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
import connect4 as c4
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

A = c4.assembly()
d0 = c4.disc()
discs = {f"disc{i}{j}": c4.disc_at(i, j, d0) for i in range(c4.COLS) for j in range(c4.ROWS)}
parts = {**A, **discs}

def vol_int(a, b):
    try:
        return a.intersect(b).val().Volume()
    except Exception:
        return 0.0

def dist(a, b):
    e = BRepExtrema_DistShapeShape(a.val().wrapped, b.val().wrapped); e.Perform()
    return e.Value()

bad = 0
names = list(parts)
for a, b in itertools.combinations(names, 2):
    if a.startswith("disc") and b.startswith("disc"):
        continue
    ba, bb = parts[a].val().BoundingBox(), parts[b].val().BoundingBox()
    if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
            or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
        continue
    v = vol_int(parts[a], parts[b])
    if v > 1e-3:
        bad += 1
        print(f"INTERFERENCE {a} x {b}: {v:.3f} mm^3")
print("interferences:", bad)

frame = A["front"].union(A["back"])
md = min(dist(discs[k], frame) for k in discs)
print(f"min disc-to-frame gap (all 42 discs): {md:.3f} mm")
print(f"disc vs channel: width {c4.CHAN_W - c4.DISC_D:.2f} mm total, depth {c4.CHAN_D - c4.DISC_T:.2f} mm total")
print(f"disc overlaps window edge (retention): {(c4.DISC_D - c4.WIN_H) / 2:.2f} mm top+bottom")
print(f"bar-to-frame gap: {dist(A['bar'], frame):.3f} mm")
# bar can be pulled fully out to the right without hitting the right foot
pulled = A["bar"].translate((c4.BAR_L + 5, 0, 0))
print("bar pulled-out path vs right foot:", f"{vol_int(A['bar'].translate((150,0,0)), A['footR']):.3f}",
      f"{vol_int(pulled, A['footR']):.3f}", "mm^3 (0 = clear)")
print("bar path vs right clamp:", f"{vol_int(A['bar'].translate((100,0,0)), A['clampR']):.3f}")
# peg engagement
print("peg fit: peg", c4.PEG_D, "in hole", c4.PEG_HOLE_D, "->", (c4.PEG_HOLE_D - c4.PEG_D) / 2, "mm per side")
# clamps grip the frame: legs touch plates
print(f"clamp L to frame gap: {dist(A['clampL'], frame):.3f} mm  (snap bumps sit in grooves)")
print(f"frame-in-foot pocket clearance per side: {c4.CLR} mm")
