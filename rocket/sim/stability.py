# Stability (Barrowman CP + extended body-lift check) for the single-stage C6 FPV rocket.
# CG of printed parts comes from the exported STLs (true geometry), other parts are listed below.
# Usage:  python3 stability.py body.stl payload.stl nose.stl
# Positions are mm measured UP from the tail (z = 0 at the aft end of the body).
import math, sys

# ---- geometry (keep in sync with c6_fpv_rocket.scad) -----------------------
body_len, shoulder_len, trans_len, pay_len = 107, 12, 18, 33
nose_len, nose_shoulder, tip_round = 75, 8, 2.0
d_body, d_bay = 20.0, 33.2
n_fins, Cr, Ct, span, sweep, fin_t = 4, 55, 20, 36, 28, 1.4
PLA = 1.24                                    # g/cm3 (PETG ~1.27)

z_pay  = body_len - shoulder_len              # payload part origin
z_flare0, z_flare1 = body_len, body_len + trans_len
z_bay1 = z_flare1 + pay_len                   # top of bay = nose base
z_nose = z_bay1
# Haack radius, x measured from the virtual tip
def haack_r(x):
    th = math.acos(1 - 2*min(max(x, 0), nose_len)/nose_len)
    return d_bay/2/math.sqrt(math.pi)*math.sqrt(th - math.sin(2*th)/2)
x_cut = next(x/100 for x in range(0, nose_len*100) if haack_r(x/100) >= tip_round)
z_tip = z_nose + nose_len - x_cut + tip_round
L = z_tip                                     # overall length

# ---- STL mass properties ----------------------------------------------------
def stl_props(path):
    v = [tuple(map(float, l.split()[1:])) for l in open(path) if l.strip().startswith("vertex")]
    V = cz = 0.0
    for a, b, c in zip(v[0::3], v[1::3], v[2::3]):
        dv = (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0]) + a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        V += dv; cz += dv*(a[2]+b[2]+c[2])/4
    return abs(V)/1000*PLA, cz/V

body_stl, pay_stl, nose_stl = sys.argv[1:4]
mb, zb = stl_props(body_stl)
mp, zp_ = stl_props(pay_stl);  zp_ += z_pay
mn, zn_ = stl_props(nose_stl); zn_ += z_nose - nose_shoulder   # exported shifted up by the shoulder

parts = {   # name: (grams, z of its centre)
    "body + fins (printed)":   (mb, zb),
    "payload bay (printed)":   (mp, zp_),
    "nose + pod (printed)":    (mn, zn_),
    "VTX board":               (6.0, z_pay + 30 + 15.25),
    "1S battery ~150 mAh":     (4.0, z_pay + 30 + 16),
    "camera":                  (3.0, z_nose + 13.2),
    "coax + power leads":      (1.0, z_nose - 8),
    "streamer+kevlar+wadding": (3.0, 90),
    "glue / tape":             (1.0, z_pay + 10),
}
C6_full, C6_empty, z_motor = 24.1, 13.3, 35.0

# ---- Barrowman CP -----------------------------------------------------------
A_ref = math.pi*(d_bay/2)**2
cps = []
cps.append(("nose (Haack)", 2.0, z_tip - 0.500*(z_tip - z_nose)))
# flare: diameter shrinks going aft -> negative normal force
r = d_bay/d_body
CNt = 2*((d_body/d_bay)**2 - 1)
x_t = trans_len/3*(1 + (1 - r)/(1 - r*r))           # from the flare's front (bay end)
cps.append(("flare (bay -> body)", CNt, z_flare1 - x_t))
R = d_body/2
lf = math.hypot(span, sweep + Ct/2 - Cr/2)
CNf = (1 + R/(span + R))*(4*n_fins*(span/d_bay)**2)/(1 + math.sqrt(1 + (2*lf/(Cr + Ct))**2))
x_f = sweep*(Cr + 2*Ct)/(3*(Cr + Ct)) + (Cr + Ct - Cr*Ct/(Cr + Ct))/6   # aft of root LE
cps.append(("fins x%d" % n_fins, CNf, Cr - x_f))

def cp_of(items):
    CN = sum(c for _, c, _ in items)
    return CN, sum(c*z for _, c, z in items)/CN

CN0, CP0 = cp_of(cps)

# ---- extended check: body lift (Galejs, K=1.1) at 5 deg incl. camera pod ----
def planform():
    A = Az = 0.0
    dz = 0.5; z = 0.0
    while z < z_tip:
        if   z < body_len:  w = d_body
        elif z < z_flare1:  t = (z - z_flare0)/trans_len; w = d_body + (d_bay - d_body)*(1 - math.cos(math.pi*t))/2
        elif z < z_nose:    w = d_bay
        else:               w = 2*haack_r(nose_len - (z - z_nose))
        A += w*dz; Az += w*dz*z; z += dz
    # camera pod seen side-on: ~7 mm proud over ~45 mm, centred ~18 mm above the nose base
    A += 7*45; Az += 7*45*(z_nose + 18)
    return A, Az/A
Apl, zpl = planform()
alpha = math.radians(10)
CN_body = 1.1*(Apl/A_ref)*alpha**2                  # Galejs: grows with alpha^2
cps5 = [(n, c*alpha, z) for n, c, z in cps] + [("body lift @10deg", CN_body, zpl)]
CN5, CP5 = cp_of(cps5)

# ---- report -------------------------------------------------------------------
print(f"Overall length {L:.0f} mm, ref diameter {d_bay} mm (bay), body {d_body} mm\n")
print("Mass items (g @ mm from tail):")
for k, (m, z) in parts.items(): print(f"  {k:26s} {m:5.1f} g @ {z:6.1f}")
print(f"  {'C6 motor (loaded/empty)':26s} {C6_full:5.1f} / {C6_empty:.1f} g @ {z_motor:.1f}\n")
print("CP contributions (CN_alpha @ mm from tail):")
for n, c, z in cps: print(f"  {n:22s} {c:6.2f} @ {z:6.1f}")
print(f"  {'TOTAL Barrowman CP':22s} {CN0:6.2f} @ {CP0:6.1f}   ({L - CP0:.0f} mm from tip)")
print(f"  with body lift + pod at 10 deg AoA:  CP @ {CP5:6.1f}   ({L - CP5:.0f} mm from tip)\n")
for label, mm in (("Liftoff (C6 loaded)", C6_full), ("Burnout (C6 empty)", C6_empty)):
    M = sum(m for m, _ in parts.values()) + mm
    CG = (sum(m*z for m, z in parts.values()) + mm*z_motor)/M
    for tag, cp in (("Barrowman", CP0), ("w/ body lift 10deg", CP5)):
        cal = (CG - cp)/d_bay
        print(f"{label:20s} {tag:18s} mass {M:5.1f} g  CG {L-CG:5.0f} mm from tip  CP {L-cp:5.0f} mm  "
              f"margin {cal:4.2f} cal ({(CG-cp)/d_body:4.2f} body cal, {100*(CG-cp)/L:4.1f}% of length)")
# how much nose weight for 1.5 cal at liftoff (Barrowman)?
M0 = sum(m for m, _ in parts.values()) + C6_full
CG0 = (sum(m*z for m, z in parts.values()) + C6_full*z_motor)/M0
target = CP0 + 1.5*d_bay
z_w = z_tip - 15
w = max(0.0, (target*M0 - CG0*M0)/(z_w - target))
print(f"\nNose weight (in the tip) to reach 1.5 cal at liftoff: {w:.1f} g")
