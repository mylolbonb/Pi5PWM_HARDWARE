# Single-stage altitude sim: Estes C6, vertical flight, ISA air.
# Thrust curve from thrustcurve.org.
# Usage: python3 altitude_sim.py thrustcurves_C11_C6.json <dry_mass_g> [ref_diameter_mm]
import json, math, sys
d = json.load(open(sys.argv[1]))
c6 = None
for r in d['results']:
    if r['motorId'].endswith('15') and (c6 is None or r.get('source') == 'cert'):
        c6 = [(s['time'], s['thrust']) for s in r['samples']]

def thrust(t):
    if t <= 0 or t >= c6[-1][0]: return 0.0
    p = (0.0, 0.0)
    for q in c6:
        if q[0] >= t:
            return p[1] + (q[1]-p[1])*(t-p[0])/(q[0]-p[0]) if q[0] > p[0] else q[1]
        p = q
    return 0.0

I6 = 0; p = (0, 0)
for q in c6: I6 += (q[0]-p[0])*(q[1]+p[1])/2; p = q

def rho(h):
    T = 288.15 - 0.0065*h; return 1.225*(T/288.15)**4.2559

def run(cd, dry, dref, g=9.81, dt=0.0005):
    A = math.pi*(dref/2000)**2
    m6, p6 = 0.0241, 0.0108
    t = h = v = I = vmax = 0.0
    while True:
        F = thrust(t); I += F*dt
        m = dry + m6 - p6*I/I6
        a = (F - 0.5*rho(h)*v*abs(v)*cd*A)/m - g
        if h <= 0 and a < 0: a = 0
        v += a*dt; h += v*dt; t += dt
        vmax = max(vmax, v)
        if v < 0 and t > 0.5:
            return h, t, vmax, t - c6[-1][0]

dry = float(sys.argv[2])/1000
dref = float(sys.argv[3]) if len(sys.argv) > 3 else 33.2
print(f"dry {dry*1000:.1f} g, liftoff {(dry+0.0241)*1000:.1f} g, ref dia {dref} mm, C6 {I6:.2f} Ns / {c6[-1][0]:.2f} s")
for cd in (0.5, 0.65, 0.8):
    h, t, vm, coast = run(cd, dry, dref)
    print(f"Cd {cd}: apogee {h:.0f} m ({h*3.281:.0f} ft), max v {vm:.0f} m/s ({vm*3.6:.0f} km/h), "
          f"apogee at {t:.1f} s, coast after burnout {coast:.1f} s")
