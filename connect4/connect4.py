"""Printable Connect 4 — parametric CadQuery model.

Every part fits a 250 x 250 mm bed and prints without supports.
Run:  python3 connect4.py   -> writes STEP + STL files into ./step and ./stl
"""
import os
import cadquery as cq

# ---------------- parameters (mm) ----------------
COLS, ROWS = 7, 6
DISC_D, DISC_T = 30.0, 6.0
PITCH_X = 34.0            # column pitch
PITCH_Z = 30.0            # row pitch (discs stack on each other)
CHAN_W = 30.8             # column channel width
RIB_W = PITCH_X - CHAN_W  # 3.2
CHAN_D = 7.5              # channel depth (gap between plates)
PLATE_T = 2.5
HALF_T = PLATE_T + CHAN_D / 2           # 6.25  (one printed half)
FRAME_T = 2 * HALF_T                    # 12.5
WALL_W = (250.0 - COLS * CHAN_W - (COLS - 1) * RIB_W) / 2  # 7.6 -> frame 250 wide
FRAME_W = 250.0
BAR_Z0, BAR_Z1 = 12.0, 20.0             # release-bar slot
STACK_TOP = BAR_Z1 + ROWS * PITCH_Z     # 200
FRAME_H = STACK_TOP + 12.0              # 212
WINDOW_D = 26.0
PEG_D, PEG_HOLE_D, PEG_L = 4.0, 4.4, 3.5
PEG_Z = [6.0, 60.0, 120.0, 180.0]
CLR = 0.2

def col_x(i):
    return WALL_W + CHAN_W / 2 + i * PITCH_X

def row_z(j):
    return BAR_Z1 + PITCH_Z / 2 + j * PITCH_Z

# ---------------- frame half (print twice) ----------------
def frame_half():
    # front plate lies on the bed (y = 0 .. PLATE_T)
    plate = cq.Workplane("XY").box(FRAME_W, PLATE_T, FRAME_H, centered=False)
    holes = [(col_x(i), row_z(j)) for i in range(COLS) for j in range(ROWS)]
    cutter = (cq.Workplane("XZ").pushPoints(holes).circle(WINDOW_D / 2)
              .extrude(-FRAME_T * 3).translate((0, -FRAME_T, 0)))
    plate = plate.cut(cutter)

    body = plate
    depth = HALF_T - PLATE_T
    # outer walls
    for x0 in (0.0, FRAME_W - WALL_W):
        body = body.union(cq.Workplane("XY").box(WALL_W, depth, FRAME_H, centered=False)
                          .translate((x0, PLATE_T, 0)))
    # ribs between columns
    for i in range(COLS - 1):
        x0 = WALL_W + CHAN_W + i * PITCH_X
        body = body.union(cq.Workplane("XY").box(RIB_W, depth, FRAME_H, centered=False)
                          .translate((x0, PLATE_T, 0)))
    # release-bar slot through walls and ribs (open towards mating face -> no bridging)
    slot = (cq.Workplane("XY").box(FRAME_W + 2, depth + 1, BAR_Z1 - BAR_Z0, centered=False)
            .translate((-1, PLATE_T, BAR_Z0)))
    body = body.cut(slot)
    # top lead-in chamfer on the ribs so discs find the column
    # alignment pegs on left wall, matching holes on right wall
    xl, xr = WALL_W / 2, FRAME_W - WALL_W / 2
    for z in PEG_Z:
        peg = (cq.Workplane("XZ").center(xl, z).circle(PEG_D / 2).extrude(-PEG_L)
               .translate((0, HALF_T, 0)))
        peg = peg.faces(">Y").chamfer(0.5)
        body = body.union(peg)
        hole = (cq.Workplane("XZ").center(xr, z).circle(PEG_HOLE_D / 2).extrude(-(PEG_L + 0.5))
                .translate((0, HALF_T - PEG_L - 0.5, 0)))
        body = body.cut(hole)
    # finger chamfer on the top front edge
    body = body.edges("|X and >Z and <Y").chamfer(1.0)
    return body

# ---------------- release bar ----------------
BAR_Y = CHAN_D - 0.5          # 7.0
BAR_H = BAR_Z1 - BAR_Z0 - 0.5 # 7.5
BAR_L = 244.0
def release_bar():
    bar = cq.Workplane("XY").box(BAR_L, BAR_Y, BAR_H, centered=False)
    grip = (cq.Workplane("XY").box(5.0, BAR_Y, 32.0, centered=False)
            .translate((BAR_L, 0, 0)))
    grip = grip.edges("|Y and >Z").fillet(2.4)
    bar = bar.union(grip)
    bar = bar.faces("<X").edges("|Y").chamfer(1.5)   # lead-in nose
    return bar

# ---------------- foot (print twice) ----------------
FOOT_LEN = 140.0
FOOT_BASE_T = 5.0
LIFT = 25.0           # frame bottom height above table
CHEEK_T = 5.0
POCKET_D = 20.0
def foot():
    pocket_t = FRAME_T + 2 * CLR
    x_out, x_in = -14.0, 40.0
    base = (cq.Workplane("XY").box(x_in - x_out, FOOT_LEN, FOOT_BASE_T, centered=False)
            .translate((x_out, -FOOT_LEN / 2, 0)))
    base = base.edges("|Z").fillet(8)
    # pedestal under the frame's side wall
    ped = (cq.Workplane("XY").box(WALL_W + CLR - x_out, pocket_t + 2 * CHEEK_T, LIFT, centered=False)
           .translate((x_out, -(pocket_t / 2 + CHEEK_T), 0)))
    cheek_h = LIFT + POCKET_D
    cheeks = None
    for s in (-1, 1):
        y0 = pocket_t / 2 if s > 0 else -(pocket_t / 2 + CHEEK_T)
        c = (cq.Workplane("XY").box(x_in - x_out, CHEEK_T, cheek_h, centered=False)
             .translate((x_out, y0, 0)))
        c = c.edges("|Y and >Z and >X").fillet(10)
        cheeks = c if cheeks is None else cheeks.union(c)
    # gussets for stiffness
    gus = None
    for s in (-1, 1):
        y0 = pocket_t / 2 + CHEEK_T if s > 0 else -(pocket_t / 2 + CHEEK_T) - 30
        g = (cq.Workplane("YZ").polyline([(0, 0), (30, 0), (0, cheek_h - 5)]).close()
             .extrude(4).translate((x_out, 0, 0)))
        if s > 0:
            g = g.translate((0, y0, 0))
        else:
            g = g.mirror("XZ").translate((0, -(pocket_t / 2 + CHEEK_T), 0))
        gus = g if gus is None else gus.union(g)
    f = base.union(ped).union(cheeks).union(gus)
    # outer end wall to stop the frame sliding sideways
    end = (cq.Workplane("XY").box(4, pocket_t + 2 * CHEEK_T, cheek_h, centered=False)
           .translate((x_out, -(pocket_t / 2 + CHEEK_T), 0)))
    f = f.union(end)
    return f

# ---------------- disc (print 21 + 21) ----------------
def disc():
    d = cq.Workplane("XY").circle(DISC_D / 2).extrude(DISC_T)
    d = d.edges().chamfer(0.6)
    ring = (cq.Workplane("XY").circle(DISC_D / 2 - 3).circle(DISC_D / 2 - 4.5)
            .extrude(0.6).translate((0, 0, DISC_T - 0.6)))
    d = d.cut(ring)
    return d

PARTS = {
    "frame_half_x2": frame_half,
    "release_bar_x1": release_bar,
    "foot_x2": foot,
    "disc_x42": disc,
}

def assembly():
    """Parts placed in their playing position (for renders)."""
    a = {}
    fh = frame_half().translate((0, 0, LIFT))
    a["front"] = fh
    a["back"] = frame_half().rotate((FRAME_W / 2, 0, 0), (FRAME_W / 2, 0, 1), 180) \
        .translate((0, FRAME_T, LIFT))
    a["bar"] = release_bar().translate((FRAME_W - BAR_L, PLATE_T + 0.25, LIFT + BAR_Z0 + 0.25))
    yc = FRAME_T / 2
    a["footL"] = foot().translate((0, yc, 0))
    a["footR"] = foot().rotate((0, 0, 0), (0, 0, 1), 180).translate((FRAME_W, yc, 0))
    return a

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for sub in ("step", "stl"):
        os.makedirs(os.path.join(here, sub), exist_ok=True)
    for name, fn in PARTS.items():
        s = fn()
        bb = s.val().BoundingBox()
        print(f"{name:18s} {bb.xlen:7.1f} x {bb.ylen:7.1f} x {bb.zlen:7.1f}  valid={s.val().isValid()}")
        cq.exporters.export(s, os.path.join(here, "step", f"{name}.step"))
        cq.exporters.export(s, os.path.join(here, "stl", f"{name}.stl"), tolerance=0.05)
