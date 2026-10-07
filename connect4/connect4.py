"""Printable Connect 4 — parametric CadQuery model.

Every part fits a 250 x 250 mm bed and prints without supports.
Run:  python3 connect4.py   -> writes STEP + STL files into ./step and ./stl

Parts: frame half x2, side clamp x2, foot x2, release bar x1, disc x42.
"""
import os
import cadquery as cq

# ---------------- parameters (mm) ----------------
COLS, ROWS = 7, 6
DISC_D, DISC_T = 29.0, 3.0
PITCH_X = 34.0            # column pitch
PITCH_Z = DISC_D          # row pitch (discs stack on each other)
CHAN_W = 32.0             # column channel width  -> 1.5 mm clearance per side
RIB_W = PITCH_X - CHAN_W  # 2.0
CHAN_D = 4.5              # gap between plates    -> 0.75 mm clearance per side
PLATE_T = 1.2              # 6 layers @ 0.2 mm
HALF_T = PLATE_T + CHAN_D / 2           # 3.45 (one printed half)
FRAME_T = 2 * HALF_T                    # 6.9
FRAME_W = 250.0
WALL_W = (FRAME_W - COLS * CHAN_W - (COLS - 1) * RIB_W) / 2  # 7.0
BAR_Z0, BAR_Z1 = 12.0, 20.0             # release-bar slot
STACK_TOP = BAR_Z1 + ROWS * PITCH_Z     # 194
FRAME_H = STACK_TOP + 6.0               # 200
WIN_W, WIN_H, WIN_R = 30.0, 24.0, 6.0     # rounded-rect windows (disc overlaps 2.5 mm top/bottom)
PEG_D, PEG_HOLE_D, PEG_L = 3.5, 3.7, 2.5   # snug press fit
PEG_Z = [6.0, 45.0, 105.0, 165.0, 194.0]
CLR = 0.15

# side clamps (U-channels that snap over both frame edges)
CLAMP_Z0, CLAMP_Z1 = 110.0, FRAME_H
CLAMP_WALL = 1.6
CLAMP_GAP = FRAME_T + 0.1
SNAP_Z = [125.0, 185.0]           # snap bumps / grooves (frame z)
SNAP_R = 0.6                             # groove radius
SNAP_H = 0.25                            # how far the bump sticks in (safe flex for PLA/PETG)
SNAP_YC = -(SNAP_R - SNAP_H - 0.1)       # groove/bump axis, 0.1 mm proud of seated bump

def col_x(i):
    return WALL_W + CHAN_W / 2 + i * PITCH_X

def row_z(j):
    return BAR_Z1 + PITCH_Z / 2 + j * PITCH_Z

# ---------------- frame half (print twice, face down) ----------------
def frame_half():
    plate = cq.Workplane("XY").box(FRAME_W, PLATE_T, FRAME_H, centered=False)
    win = (cq.Workplane("XY").box(WIN_W, PLATE_T + 2, WIN_H).edges("|Y").fillet(WIN_R))
    body = plate
    for i in range(COLS):
        for j in range(ROWS):
            body = body.cut(win.translate((col_x(i), PLATE_T / 2, row_z(j))))
        # lightening window in the bottom band (release bar shows through)
        low = (cq.Workplane("XY").box(CHAN_W - 6, PLATE_T + 2, BAR_Z1 - 6).edges("|Y").fillet(3)
               .translate((col_x(i), PLATE_T / 2, BAR_Z1 / 2)))
        body = body.cut(low)
    # chamfer the inner edge of every window so a falling disc slides past instead of catching
    sel = None
    for i in range(COLS):
        for j in range(ROWS):
            x, z = col_x(i), row_z(j)
            bs = cq.selectors.BoxSelector((x - WIN_W / 2 - 0.05, PLATE_T - 0.05, z - WIN_H / 2 - 0.05),
                                          (x + WIN_W / 2 + 0.05, PLATE_T + 0.05, z + WIN_H / 2 + 0.05))
            sel = bs if sel is None else sel + bs
    body = body.edges(sel).chamfer(0.6)

    depth = HALF_T - PLATE_T
    for x0 in (0.0, FRAME_W - WALL_W):
        body = body.union(cq.Workplane("XY").box(WALL_W, depth, FRAME_H, centered=False)
                          .translate((x0, PLATE_T, 0)))
    for i in range(COLS - 1):
        x0 = WALL_W + CHAN_W + i * PITCH_X
        rib = (cq.Workplane("XY").box(RIB_W, depth, FRAME_H, centered=False)
               .edges("|Y and >Z").chamfer(0.9)          # pointed top = disc lead-in
               .translate((x0, PLATE_T, 0)))
        body = body.union(rib)
    # release-bar slot (open towards the mating face -> no bridging)
    slot = (cq.Workplane("XY").box(FRAME_W + 2, depth + 1, BAR_Z1 - BAR_Z0, centered=False)
            .translate((-1, PLATE_T, BAR_Z0)))
    body = body.cut(slot)
    # pegs on the left wall, holes on the right wall -> two identical halves mate
    xl, xr = WALL_W / 2, FRAME_W - WALL_W / 2
    for z in PEG_Z:
        peg = (cq.Workplane("XZ").center(xl, z).circle(PEG_D / 2).extrude(-PEG_L)
               .translate((0, HALF_T, 0)))
        body = body.union(peg.faces(">Y").chamfer(0.5))
        hole = (cq.Workplane("XZ").center(xr, z).circle(PEG_HOLE_D / 2).extrude(-(PEG_L + 0.5))
                .translate((0, HALF_T - PEG_L - 0.5, 0)))
        body = body.cut(hole)
    # snap grooves on the outer face of both side walls (side clamps click in here)
    for z in SNAP_Z:
        g = (cq.Workplane("YZ").center(0, z).circle(SNAP_R).extrude(FRAME_W + 2)
             .translate((-1, SNAP_YC, 0)))
        for x0 in (0.0, FRAME_W - WALL_W + 1.0):
            keep = (cq.Workplane("XY").box(WALL_W - 1.0, 5, 5, centered=(False, True, True))
                    .translate((x0, 0, z)))
            body = body.cut(g.intersect(keep))
    body = body.edges("|X and >Z and <Y").chamfer(1.0)
    return body

# ---------------- side clamp (print twice, outer face down) ----------------
def side_clamp():
    """U-channel that slides sideways over the left/right frame edge and clicks
    into the grooves, locking the two halves together. Modelled for the LEFT side."""
    L = CLAMP_Z1 - CLAMP_Z0
    depth = WALL_W - 0.5
    outer = (cq.Workplane("XY").box(depth + CLAMP_WALL, CLAMP_GAP + 2 * CLAMP_WALL, L, centered=False)
             .translate((-CLAMP_WALL, -CLAMP_WALL - 0.05, CLAMP_Z0)))
    inner = (cq.Workplane("XY").box(depth + 1, CLAMP_GAP, L + 2, centered=False)
             .translate((0, -0.05, CLAMP_Z0 - 1)))
    c = outer.cut(inner)
    c = c.edges("|Z and <X").fillet(1.2)
    # snap bumps on the inside of both legs
    for z in SNAP_Z:
        for y_face, sgn in ((-0.05, 1), (FRAME_T + 0.05, -1)):
            yc = SNAP_YC if sgn > 0 else FRAME_T - SNAP_YC
            b = (cq.Workplane("YZ").center(0, z).circle(SNAP_R - 0.15).extrude(depth - 2.0)
                 .translate((1.0, yc, 0)))
            c = c.union(b.intersect(outer))
    # lead-in chamfers on the leg tips so it pushes on easily
    c = c.faces(">X").edges("|Z").chamfer(0.5)
    return c

# ---------------- release bar ----------------
BAR_Y = CHAN_D - 0.7           # 4.3
BAR_H = BAR_Z1 - BAR_Z0 - 0.6  # 7.4
GRIP_T = 4.0
BAR_L = FRAME_W - GRIP_T - 0.0 # 246 -> part is exactly 250 long
BAR_X0 = FRAME_W - BAR_L       # inserted position: left end sits inside the left wall
def release_bar():
    bar = cq.Workplane("XY").box(BAR_L, BAR_Y, BAR_H, centered=False)
    grip = (cq.Workplane("XY").box(GRIP_T, BAR_Y, 32.0, centered=False)
            .translate((BAR_L, 0, 0)))
    grip = grip.edges("|Y and >Z").fillet(1.9)
    bar = bar.union(grip)
    bar = bar.faces("<X").edges("|Y").chamfer(1.5)
    return bar

# ---------------- foot (print twice) ----------------
FOOT_LEN = 120.0
FOOT_T = 2.4          # wall / plate thickness
LIFT = 25.0           # frame bottom height above the table
POCKET_D = 15.0
def foot():
    """Light open-frame foot: a beam along the table, two cheeks gripping the
    frame, an end wall (notched for the release bar), a shelf the frame stands
    on (7 mm bridge) and two gussets."""
    t = FOOT_T
    pocket_t = FRAME_T + 2 * CLR
    x_out, x_in = -10.0, 28.0
    cheek_h = LIFT + POCKET_D
    yc = pocket_t / 2 + t                     # outer face of the cheeks
    beam = (cq.Workplane("XY").box(16, FOOT_LEN, t, centered=False)
            .translate((x_out, -FOOT_LEN / 2, 0)).edges("|Z").fillet(5))
    f = beam
    for s in (-1, 1):
        y0 = pocket_t / 2 if s > 0 else -yc
        c = (cq.Workplane("XY").box(x_in - x_out, t, cheek_h, centered=False)
             .translate((x_out, y0, 0)))
        f = f.union(c.edges("|Y and >Z and >X").fillet(8))
    end = cq.Workplane("XY").box(t, 2 * yc, cheek_h, centered=False).translate((x_out, -yc, 0))
    shelf = (cq.Workplane("XY").box(WALL_W + CLR - x_out, pocket_t, t, centered=False)
             .translate((x_out, -pocket_t / 2, LIFT - t)))
    f = f.union(end).union(shelf)
    reach = FOOT_LEN / 2 - yc
    for xg in (x_out,):
        for s in (-1, 1):
            g = (cq.Workplane("YZ").polyline([(0, 0), (reach, 0), (0, cheek_h - 8)]).close()
                 .extrude(t))
            g = g.translate((xg, yc, 0)) if s > 0 else g.mirror("XZ").translate((xg, -yc, 0))
            f = f.union(g)
    nw = CHAN_D + 1.0
    notch = (cq.Workplane("XY").box(30, nw, cheek_h, centered=False)
             .translate((x_out - 5, -nw / 2, LIFT + BAR_Z0 - 1.0)))
    return f.cut(notch)

# ---------------- disc (print 21 + 21) ----------------
def disc():
    d = cq.Workplane("XY").circle(DISC_D / 2).extrude(DISC_T)
    d = d.edges().chamfer(0.5)
    ring = (cq.Workplane("XY").circle(DISC_D / 2 - 3).circle(DISC_D / 2 - 4.5)
            .extrude(0.4).translate((0, 0, DISC_T - 0.4)))
    return d.cut(ring)

PARTS = {
    "frame_half_x2": frame_half,
    "side_clamp_x2": side_clamp,
    "foot_x2": foot,
    "release_bar_x1": release_bar,
    "disc_x42": disc,
}

def assembly():
    """Parts placed in playing position (frame bottom LIFT mm above the table)."""
    a = {}
    a["front"] = frame_half().translate((0, 0, LIFT))
    a["back"] = (frame_half().rotate((FRAME_W / 2, 0, 0), (FRAME_W / 2, 0, 1), 180)
                 .translate((0, FRAME_T, LIFT)))
    a["bar"] = release_bar().translate((BAR_X0, PLATE_T + (CHAN_D - BAR_Y) / 2, LIFT + BAR_Z0 + 0.1))
    a["clampL"] = side_clamp().translate((0, 0, LIFT))
    a["clampR"] = (side_clamp().rotate((0, 0, 0), (0, 0, 1), 180)
                   .translate((FRAME_W, FRAME_T, LIFT)))
    yc = FRAME_T / 2
    a["footL"] = foot().translate((0, yc, 0))
    a["footR"] = foot().rotate((0, 0, 0), (0, 0, 1), 180).translate((FRAME_W, yc, 0))
    return a

def disc_at(i, j, d=None):
    d = d or disc()
    y = PLATE_T + (CHAN_D - DISC_T) / 2
    return (d.rotate((0, 0, 0), (1, 0, 0), -90)
            .translate((col_x(i), y, LIFT + row_z(j))))

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for sub in ("step", "stl"):
        os.makedirs(os.path.join(here, sub), exist_ok=True)
    for name, fn in PARTS.items():
        s = fn()
        bb = s.val().BoundingBox()
        print(f"{name:18s} {bb.xlen:7.1f} x {bb.ylen:7.1f} x {bb.zlen:7.1f}  valid={s.val().isValid()}  solids={len(s.solids().vals())}")
        cq.exporters.export(s, os.path.join(here, "step", f"{name}.step"))
        cq.exporters.export(s, os.path.join(here, "stl", f"{name}.stl"), tolerance=0.05)
