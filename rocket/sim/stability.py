# Rough Barrowman CP + CG estimate for the single-stage C6 FPV rocket.
# Positions in mm from the nose tip. Edit the masses after weighing real parts.
import math
d_ref, d_body = 33.2, 20.0
L_nose, L_bay, L_flare, L_body = 75, 33, 18, 107
n_fins, Cr, Ct, span, sweep = 4, 55, 20, 36, 28

x_bay, x_flare, x_body = L_nose, L_nose + L_bay, L_nose + L_bay + L_flare
x_tail = x_body + L_body
# nose (ogive)
CN_n, X_n = 2.0, 0.466*L_nose
# flare: diameter shrinks going aft -> negative lift
r = d_ref/d_body
CN_t = 2*((d_body/d_ref)**2 - 1)
X_t = x_flare + L_flare/3*(1 + (1 - r)/(1 - r*r))
# fins
R = d_body/2
lf = math.hypot(span, sweep + Ct/2 - Cr/2)
CN_f = (1 + R/(span + R)) * (4*n_fins*(span/d_ref)**2) / (1 + math.sqrt(1 + (2*lf/(Cr + Ct))**2))
X_f = (x_tail - Cr) + sweep*(Cr + 2*Ct)/(3*(Cr + Ct)) + (Cr + Ct - Cr*Ct/(Cr + Ct))/6
CN = CN_n + CN_t + CN_f
CP = (CN_n*X_n + CN_t*X_t + CN_f*X_f)/CN

# (mass g, position mm)
items = {
    "nose + camera pod (printed)": (10.4, 50),
    "camera":                      (3.0, 68),
    "payload bay (printed)":       (7.1, 112),
    "VTX":                         (6.0, 92),
    "1S battery":                  (4.0, 92),
    "wiring":                      (1.0, 95),
    "streamer + kevlar + wadding": (3.0, 150),
    "glue":                        (1.0, 100),
    "body + fins (printed)":       (16.6, 195),
}
motor_full, motor_empty, x_motor = 24.1, 13.3, x_tail - 35
for label, m_motor in (("loaded C6", motor_full), ("burnt-out C6", motor_empty)):
    M = sum(m for m, _ in items.values()) + m_motor
    CG = (sum(m*x for m, x in items.values()) + m_motor*x_motor)/M
    print(f"{label}: mass {M:.1f} g, CG {CG:.0f} mm, CP {CP:.0f} mm, "
          f"margin {(CP - CG)/d_ref:.2f} cal (of {d_ref} mm), {(CP - CG)/d_body:.2f} body-cal")
