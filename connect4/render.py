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
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
A = c4.assembly()
disc = c4.disc()
CLAMP_COL = (0.95, 0.95, 0.97)
BAR_COL = (0.95, 0.45, 0.10)

def disc_in_board(i, j, red):
    return actor(c4.disc_at(i, j, disc), RED if red else YEL)

frame_parts = [actor(A["front"], FRAME_COL), actor(A["back"], FRAME_COL),
               actor(A["clampL"], CLAMP_COL), actor(A["clampR"], CLAMP_COL),
               actor(A["footL"], GREY), actor(A["footR"], GREY)]
moves = [(3,0,1),(3,1,0),(2,0,1),(4,0,0),(4,1,1),(5,0,0),(1,0,1),(3,2,0),(2,1,1),(5,1,0),(2,2,1),(6,0,0)]
discs = [disc_in_board(*m) for m in moves]
loose = [actor(disc.translate((40 + k * 36, -95, 0)), RED if k % 2 else YEL) for k in range(4)]
bar_in = actor(A["bar"], BAR_COL)
c = (125, 6, 125)
render(frame_parts + [bar_in] + discs + loose, "01_assembled_front.png", (-180, -620, 420), c, zoom=1.15,
       title="Connect 4 - assembled (white = side clamps, orange = release bar)")
render(frame_parts + [bar_in] + discs, "02_assembled_back.png", (480, 640, 300), c, zoom=1.2, title="Back view")

# exploded
ex = [actor(A["front"].translate((0, -120, 0)), FRAME_COL), actor(A["back"].translate((0, 120, 0)), FRAME_COL),
      actor(A["clampL"].translate((-80, 0, 30)), CLAMP_COL), actor(A["clampR"].translate((80, 0, 30)), CLAMP_COL),
      actor(A["bar"].translate((120, 0, 0)), BAR_COL), actor(A["footL"].translate((-70, 0, -40)), GREY),
      actor(A["footR"].translate((70, 0, -40)), GREY)]
render(ex, "03_exploded.png", (-520, -420, 330), c, zoom=1.2,
       title="Exploded: 2 frame halves, 2 side clamps, release bar, 2 feet")

# clamp close-up (left side, clamp pulled off a bit)
fr = [actor(A["front"], FRAME_COL), actor(A["back"], FRAME_COL), actor(A["footL"], GREY)]
cl = A["clampL"].translate((-25, 0, 0))
render(fr + [actor(cl, CLAMP_COL), edges_actor(cl)], "04_clamp_detail.png", (-160, -140, 260), (0, 6, 150),
       zoom=1.0, reset=False, title="Side clamp pushes on sideways and clicks into 3 grooves")

# inside of a half (pegs + holes + slot)
fh = c4.frame_half()
render([actor(fh, FRAME_COL), edges_actor(fh)], "05_frame_half_inside.png", (-70, 170, 120), (45, 0, 25),
       zoom=1.0, reset=False, title="Inside of a half: press-fit pegs, rib lead-ins, bar slot")

# release bar sequence
def bar_at(pull):
    return actor(A["bar"].translate((pull, 0, 0)), BAR_COL)
full = [(i, j, (i + j) % 2) for i in range(7) for j in range(3)]
stack = [disc_in_board(*m) for m in full]
render(frame_parts + [bar_at(0)] + stack, "06_bar_in.png", (420, -260, 160), (238, 6, 45),
       zoom=1.0, reset=False, title="Release bar IN - grip rests against the frame")
render(frame_parts + [bar_at(120)] + stack, "07_bar_half_out.png", (520, -420, 260), (250, 6, 60),
       zoom=1.0, reset=False, title="Pull the grip right - bar slides out through the foot notch")
dropped = [actor(disc.translate((c4.col_x(i), -40 - 33 * k, 0)), RED if (i + k) % 2 else YEL)
           for i in range(7) for k in range(3)]
render(frame_parts + [bar_at(240)] + dropped, "08_bar_out_discs_dropped.png", (-120, -700, 380), (180, 6, 90),
       zoom=1.0, title="Bar out - all discs drop. Slide it back in to play again")

# print plates (250 x 250)
def on_bed(shape, x, y):
    bb = shape.val().BoundingBox()
    return shape.translate((x - bb.xmin, y - bb.ymin, -bb.zmin))
fh_p = on_bed(fh.rotate((0, 0, 0), (1, 0, 0), 90), 0, 22)
render([actor(fh_p, FRAME_COL)], "09_plate_frame_half.png", (125, -250, 420), (125, 125, 0), zoom=1.1,
       bed=True, title="Plate 1+2: frame half (print x2) - face down, no supports")
bar_p = on_bed(c4.release_bar().rotate((0, 0, 0), (1, 0, 0), 90), 0, 5)
ft = c4.foot()
f1 = on_bed(ft, 5, 50); f2 = on_bed(ft.rotate((0, 0, 0), (0, 0, 1), 180), 65, 50)
cp = c4.side_clamp().rotate((0, 0, 0), (0, 1, 0), -90).rotate((0, 0, 0), (0, 0, 1), 90)
c1 = on_bed(cp, 130, 50); c2 = on_bed(cp, 155, 50)
dl = [actor(on_bed(disc, 185 + (k % 2) * 32, 50 + (k // 2) * 32), RED if k % 2 else YEL) for k in range(12)]
render([actor(bar_p, BAR_COL), actor(f1, GREY), actor(f2, GREY), actor(c1, CLAMP_COL), actor(c2, CLAMP_COL)] + dl,
       "10_plate_bar_feet_clamps_discs.png", (125, -250, 420), (125, 125, 0), zoom=1.1, bed=True,
       title="Plate 3: bar, 2 feet, 2 clamps, discs - no supports")
