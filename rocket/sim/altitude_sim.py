# Two-stage altitude sim: C11-0 booster -> C6 sustainer, vertical flight, ISA air.
# Thrust curves from thrustcurve.org.  Usage: python3 altitude_sim.py thrustcurves_C11_C6.json <dry_mass_g>
import json, math, sys
d = json.load(open(sys.argv[1]))
curves = {}
for r in d['results']:
    k = 'C11' if r['motorId'].endswith('1a') else 'C6'
    if k not in curves or r.get('source') == 'cert':
        curves[k] = [(s['time'], s['thrust']) for s in r['samples']]
def thrust(c, t):
    if t <= 0 or t >= c[-1][0]: return 0.0
    p = (0.0, 0.0)
    for q in c:
        if q[0] >= t:
            return p[1] + (q[1]-p[1])*(t-p[0])/(q[0]-p[0]) if q[0] > p[0] else q[1]
        p = q
    return 0.0
def impulse(c):
    I = 0; p = (0, 0)
    for q in c: I += (q[0]-p[0])*(q[1]+p[1])/2; p = q
    return I
I11, I6 = impulse(curves['C11']), impulse(curves['C6'])
def rho(h):  # ISA troposphere
    T = 288.15 - 0.0065*h; return 1.225*(T/288.15)**4.2559
def run(cd, dry, stage_delay=0.1, A=math.pi*0.0175**2, g=9.81, dt=0.0005):
    # masses in kg
    m11, p11, m6, p6 = 0.03523, 0.012, 0.0241, 0.0108
    t = h = v = 0.0; vmax = 0; I1 = I2 = 0
    t_sep = curves['C11'][-1][0]; t_ign = t_sep + stage_delay
    burn6 = curves['C6'][-1][0]; booster_on = True; out = {}
    while True:
        F1 = thrust(curves['C11'], t) if booster_on else 0
        F2 = thrust(curves['C6'], t - t_ign)
        I1 += F1*dt; I2 += F2*dt
        if booster_on and t >= t_ign: booster_on = False; out['v_stage'] = v; out['h_stage'] = h
        m = dry + (m6 - p6*I2/I6) + ((m11 - p11*I1/I11) if booster_on else 0)
        D = 0.5*rho(h)*v*abs(v)*cd*A
        a = (F1 + F2 - D)/m - g
        if t < 0.05 and a < 0: a = 0
        v += a*dt; h += v*dt; t += dt
        vmax = max(vmax, v)
        if t > t_ign + burn6 and 'burnout' not in out: out['burnout'] = (t, h, v)
        if v < 0 and t > 1:
            out.update(apogee=h, t_apo=t, vmax=vmax, coast=t - (t_ign + burn6))
            return out
dry = float(sys.argv[2])/1000
print(f"dry {dry*1000:.1f} g, liftoff {(dry+0.03523+0.0241)*1000:.1f} g")
print(f"C11 curve {I11:.2f} Ns / {curves['C11'][-1][0]:.2f} s,  C6 curve {I6:.2f} Ns / {curves['C6'][-1][0]:.2f} s")
for cd in (0.5, 0.65, 0.8):
    o = run(cd, dry)
    print(f"Cd {cd}: apogee {o['apogee']:.0f} m ({o['apogee']*3.281:.0f} ft), max v {o['vmax']:.0f} m/s ({o['vmax']*3.6:.0f} km/h), "
          f"staging at {o['h_stage']:.0f} m / {o['v_stage']:.0f} m/s, apogee {o['t_apo']:.1f} s after launch, coast after C6 burnout {o['coast']:.1f} s")
