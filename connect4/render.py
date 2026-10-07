"""Render preview images of the Connect 4 model with VTK (run under xvfb-run)."""
import os, sys
import vtk
import cadquery as cq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import connect4 as c4

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
FRAME_COL = (0.20, 0.45, 1.00)
GREY = (0.75, 0.75, 0.78)
RED, YEL = (0.85, 0.12, 0.12), (0.98, 0.82, 0.10)

def actor(shape, color, tol=0.08):
    path = "/tmp/_r.stl"
    cq.exporters.export(shape, path, tolerance=tol, angularTolerance=0.15)
    rd = vtk.vtkSTLReader(); rd.SetFileName(path); rd.Update()
    nm = vtk.vtkPolyDataNormals(); nm.SetInputConnection(rd.GetOutputPort())
    nm.SetFeatureAngle(35); nm.Update()
    pd = vtk.vtkPolyData(); pd.DeepCopy(nm.GetOutput())
    m = vtk.vtkPolyDataMapper(); m.SetInputData(pd)
    a = vtk.vtkActor(); a.SetMapper(m)
    p = a.GetProperty(); p.SetColor(*color); p.SetSpecular(0.3); p.SetSpecularPower(30); p.SetAmbient(0.30); p.SetDiffuse(0.85)
    return a

def edges_actor(shape):
    path = "/tmp/_e.stl"
    cq.exporters.export(shape, path, tolerance=0.08, angularTolerance=0.15)
    rd = vtk.vtkSTLReader(); rd.SetFileName(path)
    fe = vtk.vtkFeatureEdges(); fe.SetInputConnection(rd.GetOutputPort())
    fe.BoundaryEdgesOff(); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff()
    fe.FeatureEdgesOn(); fe.SetFeatureAngle(40)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(fe.GetOutputPort()); m.ScalarVisibilityOff()
    a = vtk.vtkActor(); a.SetMapper(m); a.GetProperty().SetColor(0.05, 0.05, 0.1)
    a.GetProperty().SetLineWidth(1.2)
    return a

def render(actors, name, cam_pos, focal, up=(0, 0, 1), size=(1600, 1200), zoom=1.0, title=None, bed=None, reset=True):
    r = vtk.vtkRenderer(); r.SetBackground(0.97, 0.97, 0.99); r.SetBackground2(0.80, 0.84, 0.92)
    r.GradientBackgroundOn()
    for a in actors: r.AddActor(a)
    if bed:  # 250x250 build-plate outline
        sq = vtk.vtkPlaneSource(); sq.SetOrigin(0, 0, -0.3); sq.SetPoint1(250, 0, -0.3); sq.SetPoint2(0, 250, -0.3)
        m = vtk.vtkPolyDataMapper(); m.SetInputConnection(sq.GetOutputPort())
        b = vtk.vtkActor(); b.SetMapper(m); b.GetProperty().SetColor(0.25, 0.25, 0.28)
        b.GetProperty().SetOpacity(0.35); r.AddActor(b)
    if title:
        t = vtk.vtkTextActor(); t.SetInput(title); tp = t.GetTextProperty()
        tp.SetFontSize(34); tp.SetColor(0.1, 0.1, 0.15); tp.BoldOn(); t.SetPosition(25, size[1] - 55)
        r.AddViewProp(t)
    cam = r.GetActiveCamera(); cam.SetPosition(*cam_pos); cam.SetFocalPoint(*focal); cam.SetViewUp(*up)
    (r.ResetCamera() if reset else r.ResetCameraClippingRange()); cam.Zoom(zoom)
    l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetPosition(0.4, 0.6, 1); l.SetIntensity(0.55); r.AddLight(l)
    w = vtk.vtkRenderWindow(); w.SetOffScreenRendering(1); w.SetSize(*size); w.SetMultiSamples(8); w.AddRenderer(r)
    w.Render()
    f = vtk.vtkWindowToImageFilter(); f.SetInput(w); f.Update()
    png = vtk.vtkPNGWriter(); png.SetFileName(os.path.join(OUT, name)); png.SetInputConnection(f.GetOutputPort()); png.Write()
    print("wrote", name)

os.makedirs(OUT, exist_ok=True)
A = c4.assembly()
disc = c4.disc()

def disc_in_board(i, j, red):
    x = c4.col_x(i); z = c4.LIFT + c4.row_z(j); y = c4.PLATE_T + (c4.CHAN_D - c4.DISC_T) / 2
    d = disc.rotate((0, 0, 0), (1, 0, 0), -90).translate((x, y, z))
    return actor(d, RED if red else YEL)

# a little game in progress: (col, row, red?)
moves = [(3,0,1),(3,1,0),(2,0,1),(4,0,0),(4,1,1),(5,0,0),(1,0,1),(3,2,0),(2,1,1),(5,1,0),(2,2,1),(6,0,0)]
base = [actor(A["front"], FRAME_COL), actor(A["back"], FRAME_COL), actor(A["bar"], GREY),
        actor(A["footL"], GREY), actor(A["footR"], GREY)]
discs = [disc_in_board(*m) for m in moves]
loose = []
for k in range(4):
    d = disc.translate((40 + k * 36, -95, 0)); loose.append(actor(d, RED if k % 2 else YEL))

c = (125, 6, 130)
render(base + discs + loose, "01_assembled_front.png", (-180, -620, 420), c, zoom=1.15,
       title="Connect 4 - assembled (game in progress)")
render(base + discs, "02_assembled_back.png", (480, 640, 300), c, zoom=1.2, title="Back view")
render(base + discs, "03_front_straight.png", (125, -900, 130), c, zoom=1.25, title="Front - 250 mm wide x 237 mm tall")

# release-bar operation sequence (right-hand side, bar pulls out to the right)
def bar_at(pull):
    return actor(A["bar"].translate((pull, 0, 0)), (0.95, 0.45, 0.10))
frame_only = [actor(A["front"], FRAME_COL), actor(A["back"], FRAME_COL),
              actor(A["footL"], GREY), actor(A["footR"], GREY)]
full = [(i, j, (i + j) % 2) for i in range(7) for j in range(3)]
stack = [disc_in_board(*m) for m in full]
render(frame_only + [bar_at(0)] + stack, "08_bar_closeup_in.png", (420, -260, 160), (238, 6, 45),
       zoom=1.0, reset=False, title="Release bar IN (orange) - grip sits in notch of foot")
render(frame_only + [bar_at(120)] + stack, "09_bar_half_out.png", (520, -420, 260), (250, 6, 60),
       zoom=1.0, reset=False, title="Pull the grip to the right - bar slides out through the notch")
dropped = []
for i in range(7):
    for k in range(3):
        x = c4.col_x(i); y = c4.FRAME_T / 2 - 3 + (k - 1) * 0.1
        d = disc.rotate((0, 0, 0), (1, 0, 0), -90).translate((x - 3 + 3 * k, -40 - 8 * k, 0))
        dropped.append(actor(disc.translate((x, -40 - 33 * k, 0)), RED if (i + k) % 2 else YEL))
render(frame_only + [bar_at(240)] + dropped, "10_bar_out_discs_dropped.png", (-120, -700, 380), (180, 6, 90),
       zoom=1.0, title="Bar fully out - all discs drop out the bottom. Slide it back in to play again")

# exploded view
ex = [actor(A["front"].translate((0, -120, 0)), FRAME_COL), actor(A["back"].translate((0, 120, 0)), FRAME_COL),
      actor(A["bar"].translate((90, 0, 0)), GREY), actor(A["footL"].translate((-70, 0, -30)), GREY),
      actor(A["footR"].translate((70, 0, -30)), GREY)]
render(ex, "04_exploded.png", (-520, -380, 330), c, zoom=1.2, title="Exploded: 2 frame halves, release bar, 2 feet")

# single half close-up of inside (ribs, slot, pegs)
fh = c4.frame_half()
render([actor(fh, FRAME_COL), edges_actor(fh)], "05_frame_half_inside.png", (-70, 170, 120), (45, 0, 25),
       zoom=1.0, reset=False, title="Frame half - inside: ribs, release-bar slot, pegs")

# print layouts (each on a 250x250 plate)
fh_print = fh.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, 0))
bb = fh_print.val().BoundingBox(); fh_print = fh_print.translate((-bb.xmin, -bb.ymin + 19, -bb.zmin))
render([actor(fh_print, FRAME_COL)], "06_print_frame_half.png", (125, -250, 420), (125, 125, 0), zoom=1.1,
       bed=True, title="Print plate: frame half (x2) - face down, no supports")

bar = c4.release_bar().rotate((0, 0, 0), (1, 0, 0), 90)
bb = bar.val().BoundingBox(); bar = bar.translate((-bb.xmin, -bb.ymin + 20, -bb.zmin))
ft = c4.foot(); bb = ft.val().BoundingBox()
f1 = ft.translate((-bb.xmin + 10, -bb.ymin + 80, 0))
f2 = ft.rotate((0, 0, 0), (0, 0, 1), 180); bb2 = f2.val().BoundingBox()
f2 = f2.translate((-bb2.xmin + 120, -bb2.ymin + 80, 0))
dl = [actor(disc.translate((178 + (k % 2) * 36, 95 + (k // 2) * 34, 0)), RED if k % 2 else YEL) for k in range(8)]
render([actor(bar, GREY), actor(f1, GREY), actor(f2, GREY)] + dl, "07_print_bar_feet_discs.png",
       (125, -250, 420), (125, 125, 0), zoom=1.1, bed=True,
       title="Print plate: release bar + 2 feet + discs - no supports")
