"""Independent checks for materi/earth/astronomy-mechanics.md.

Kepler's laws are verified by numerically integrating Newtonian orbits (velocity Verlet, units AU and years,
GM_sun = 4 pi^2) and measuring the period, the areas swept and the speeds; the formulas in the text are not used
to produce the numbers."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from earth_geosphere_astronomy_helpers import Checker

C = Checker("materi/earth/astronomy-mechanics.md")
ok = C.ok
GM_SUN = 4 * math.pi ** 2          # AU^3 / yr^2 for one solar mass


def integrate(GM, x, y, vx, vy, t_end, dt, record=None):
    """velocity Verlet; returns list of times when y crosses 0 upward (one per lap) and the final state"""
    t, crossings = 0.0, []
    r3 = (x * x + y * y) ** 1.5
    ax, ay = -GM * x / r3, -GM * y / r3
    while t < t_end:
        x += vx * dt + 0.5 * ax * dt * dt
        y += vy * dt + 0.5 * ay * dt * dt
        r3 = (x * x + y * y) ** 1.5
        nax, nay = -GM * x / r3, -GM * y / r3
        vx += 0.5 * (ax + nax) * dt
        py = y - vy * dt
        vy += 0.5 * (ay + nay) * dt
        ax, ay = nax, nay
        if record is not None:
            record(t, x, y, vx, vy)
        # upward crossing of the x-axis
        if (y - vy * dt) < 0 <= y and x > 0:
            crossings.append(t)
        t += dt
    return crossings


# ---------------- example 1: a = 4 AU -> T = 8 yr ----------------
# launch with the circular speed, count the time for one lap by tracking the angle
def lap_time(a, GM=GM_SUN, dt=1e-4):
    v = math.sqrt(GM / a)
    x, y, vx, vy = a, 0.0, 0.0, v
    t, ang, last = 0.0, 0.0, 0.0
    r3 = a ** 3
    ax, ay = -GM * x / r3, 0.0
    while True:
        x += vx * dt + 0.5 * ax * dt * dt
        y += vy * dt + 0.5 * ay * dt * dt
        r3 = (x * x + y * y) ** 1.5
        nax, nay = -GM * x / r3, -GM * y / r3
        vx += 0.5 * (ax + nax) * dt
        vy += 0.5 * (ay + nay) * dt
        ax, ay = nax, nay
        t += dt
        th = math.atan2(y, x)
        d = th - last
        if d < -math.pi: d += 2 * math.pi
        if d > math.pi: d -= 2 * math.pi
        ang += d
        last = th
        if ang >= 2 * math.pi:
            return t

T4 = lap_time(4.0)
ok(abs(T4 - 8.0) < 0.01, T4)
C.mcq("**Example 1.**", T4, "C", tol=0.02)
C.opt_is("**Example 1.**", "B", 4.0)           # T = a
C.opt_is("**Example 1.**", "D", 16.0)          # T = a^2
C.opt_is("**Example 1.**", "E", 64.0)          # forgot the square root
C.opt_is("**Example 1.**", "A", math.sqrt(4.0))

# ---------------- example 2: binary star total mass by simulating the two-body problem ----------------
def binary_period(m1, m2, sep, dt=2e-4):
    """two bodies (solar masses) at separation `sep` AU on circular orbits about their center of mass; period in years"""
    G = GM_SUN                         # per solar mass
    M = m1 + m2
    r1, r2 = sep * m2 / M, sep * m1 / M
    w = math.sqrt(G * M / sep ** 3)    # launch angular speed for a circular orbit
    x1, y1, x2, y2 = r1, 0.0, -r2, 0.0
    vx1, vy1, vx2, vy2 = 0.0, w * r1, 0.0, -w * r2
    t, ang, last = 0.0, 0.0, math.atan2(y2 - y1, x2 - x1)
    def acc(x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        r3 = (dx * dx + dy * dy) ** 1.5
        return G * m2 * dx / r3, G * m2 * dy / r3, -G * m1 * dx / r3, -G * m1 * dy / r3
    a1x, a1y, a2x, a2y = acc(x1, y1, x2, y2)
    while True:
        x1 += vx1 * dt + 0.5 * a1x * dt * dt; y1 += vy1 * dt + 0.5 * a1y * dt * dt
        x2 += vx2 * dt + 0.5 * a2x * dt * dt; y2 += vy2 * dt + 0.5 * a2y * dt * dt
        n1x, n1y, n2x, n2y = acc(x1, y1, x2, y2)
        vx1 += 0.5 * (a1x + n1x) * dt; vy1 += 0.5 * (a1y + n1y) * dt
        vx2 += 0.5 * (a2x + n2x) * dt; vy2 += 0.5 * (a2y + n2y) * dt
        a1x, a1y, a2x, a2y = n1x, n1y, n2x, n2y
        t += dt
        th = math.atan2(y2 - y1, x2 - x1)
        d = th - last
        if d < -math.pi: d += 2 * math.pi
        if d > math.pi: d -= 2 * math.pi
        ang += abs(d)
        last = th
        if ang >= 2 * math.pi:
            return t

Tb = binary_period(9.0, 4.5, 6.0)       # total 13.5 solar masses at 6 AU
ok(abs(Tb - 4.0) < 0.01, Tb)
# the brute-force inverse: which total mass gives a 4-year period at 6 AU?
M_found = min(((m / 10.0) for m in range(5, 600, 5)), key=lambda M: abs(binary_period(M * 0.6, M * 0.4, 6.0, dt=1e-3) - 4.0))
ok(abs(M_found - 13.5) < 0.3, M_found)
C.mcq("**Example 2.**", 13.5, "C")
C.opt_is("**Example 2.**", "E", 6 ** 3)
C.opt_is("**Example 2.**", "D", 6 ** 3 / 4)
C.opt_is("**Example 2.**", "B", 6 ** 2 / 4)
C.opt_is("**Example 2.**", "A", 6 / 4)

# ---------------- Q1: T = 27 yr -> a = 9 AU ----------------
T9 = lap_time(9.0, dt=2e-4)
ok(abs(T9 - 27.0) < 0.05, T9)
C.mcq("**1.**", 9.0, "C")
C.opt_is("**1.**", "A", 27 ** (1 / 3)); C.opt_is("**1.**", "B", math.sqrt(27), tol=0.02)
C.opt_is("**1.**", "D", 27.0); C.opt_is("**1.**", "E", 729.0)

# ---------------- Q2 & law 2: eccentric orbit, speeds and areas ----------------
a, e = 1.0, 0.6
rp = a * (1 - e)
vp = math.sqrt(GM_SUN * (1 + e) / (a * (1 - e)))       # launch speed at perihelion for semi-major axis a (vis-viva)
samples = []
def rec(t, x, y, vx, vy):
    samples.append((t, x, y, math.hypot(vx, vy), math.hypot(x, y)))
integrate(GM_SUN, rp, 0.0, 0.0, vp, 1.05, 1e-4, rec)
sp_max = max(samples, key=lambda s: s[3]); sp_min = min(samples, key=lambda s: s[3])
ok(abs(sp_max[4] - rp) < 1e-3 and abs(sp_min[4] - a * (1 + e)) < 5e-3, (sp_max[4], sp_min[4]))   # fastest at perihelion, slowest at aphelion
ok(abs(sp_max[3] / sp_min[3] - (1 + e) / (1 - e)) < 0.02, "speed ratio equals ra/rp")
def swept_area(t0, t1):
    pts = [s for s in samples if t0 <= s[0] < t1]
    return sum(0.5 * abs(p[1] * q[2] - p[2] * q[1]) for p, q in zip(pts, pts[1:]))
T_ecc = math.sqrt(a ** 3)
a_peri = swept_area(0.0, 0.05)
a_aph = swept_area(T_ecc / 2 - 0.025, T_ecc / 2 + 0.025)
ok(abs(a_peri - a_aph) / a_peri < 0.01, (a_peri, a_aph))
C.choice("**2.**", "E", lambda t: t == "At perihelion")
ok(abs(T_ecc - 1.0) < 1e-12)

# ---------------- Q3: force ratio ----------------
F = lambda m1, m2, r: m1 * m2 / r ** 2
ratio = F(3, 1, 2) / F(1, 1, 1)
ok(abs(ratio - 0.75) < 1e-12)
C.choice("**3.**", "A", lambda t: t == "3/4 as large")
ok(F(3, 1, 1) / F(1, 1, 1) == 3 and abs(F(3, 1, 2 ** 1.5)) > 0)
ok(abs(3 / 2 ** 3 - 3 / 8) < 1e-12)

# ---------------- Q4: Doppler ----------------
c_kms = 3.0e5
lam0, lam = 656.3, 658.5
v = c_kms * (lam - lam0) / lam0
ok(abs(v - 1005.6) < 1.0, v)
ok(lam > lam0, "redshift = receding")
def q4(t):
    return t.startswith("The galaxy recedes") and "1,000" in t
C.choice("**4.**", "D", q4)

# ---------------- Q5: simulate a 3:1 binary: orbit radii and speeds about the COM ----------------
m1, m2, sep = 3.0, 1.0, 1.0
G = GM_SUN
M = m1 + m2
r1, r2 = sep * m2 / M, sep * m1 / M
w = math.sqrt(G * M / sep ** 3)
ok(abs(r1 / r2 - 1 / 3) < 1e-12 and abs(w * r1 / (w * r2) - 1 / 3) < 1e-12)
# check by integrating: the COM stays fixed and star 1 (heavy) stays at distance r1
x1, y1, x2, y2 = r1, 0.0, -r2, 0.0
vx1, vy1, vx2, vy2 = 0.0, w * r1, 0.0, -w * r2
dt = 1e-4
def acc(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    r3 = (dx * dx + dy * dy) ** 1.5
    return G * m2 * dx / r3, G * m2 * dy / r3, -G * m1 * dx / r3, -G * m1 * dy / r3
a1x, a1y, a2x, a2y = acc(x1, y1, x2, y2)
rmax1 = rmax2 = 0.0
for _ in range(int(1.0 / dt)):
    x1 += vx1 * dt + 0.5 * a1x * dt * dt; y1 += vy1 * dt + 0.5 * a1y * dt * dt
    x2 += vx2 * dt + 0.5 * a2x * dt * dt; y2 += vy2 * dt + 0.5 * a2y * dt * dt
    n1x, n1y, n2x, n2y = acc(x1, y1, x2, y2)
    vx1 += 0.5 * (a1x + n1x) * dt; vy1 += 0.5 * (a1y + n1y) * dt
    vx2 += 0.5 * (a2x + n2x) * dt; vy2 += 0.5 * (a2y + n2y) * dt
    a1x, a1y, a2x, a2y = n1x, n1y, n2x, n2y
    cx_, cy_ = (m1 * x1 + m2 * x2) / M, (m1 * y1 + m2 * y2) / M
    rmax1 = max(rmax1, math.hypot(x1 - cx_, y1 - cy_)); rmax2 = max(rmax2, math.hypot(x2 - cx_, y2 - cy_))
ok(abs(rmax1 / rmax2 - 1 / 3) < 0.01, rmax1 / rmax2)
ok(abs(math.hypot(vx1, vy1) / math.hypot(vx2, vy2) - 1 / 3) < 0.01)
C.choice("**5.**", "B", lambda t: t == "an orbit 3 times smaller and a speed 3 times smaller")

# ---------------- facts in the text ----------------
PLANETS = {"Mercury": (0.387, 0.2408), "Venus": (0.723, 0.6152), "Earth": (1.0, 1.0), "Mars": (1.524, 1.881),
           "Jupiter": (5.203, 11.86), "Saturn": (9.537, 29.46), "Uranus": (19.19, 84.01), "Neptune": (30.07, 164.8)}
ok(all(abs(T ** 2 / a ** 3 - 1) < 0.01 for a, T in PLANETS.values()), "T^2 = a^3 for every planet")
ok(abs(PLANETS["Mercury"][1] * 365.25 - 88) < 1 and abs(PLANETS["Neptune"][1] - 165) < 1)
v_earth = 2 * math.pi * 1.495978707e8 / (365.25636 * 86400)
ok(abs(v_earth - 29.8) < 0.1, v_earth)
v_esc_earth = math.sqrt(2 * 6.674e-11 * 5.972e24 / 6.371e6) / 1000
ok(abs(v_esc_earth - 11.2) < 0.05, v_esc_earth)
ok(abs(math.sqrt(2) - 1.41) < 0.005)
ok(abs(a * (1 - 0.0167) - 0.9833) < 1e-3)
C.fact_checks([
    ("Mercury finishes one lap around the Sun in 88 days", abs(PLANETS["Mercury"][1] * 365.25 - 88) < 1, "planetary fact sheet"),
    ("Neptune needs about 165 years", abs(PLANETS["Neptune"][1] - 165) < 1, "planetary fact sheet"),
    ("Earth has e = 0.017", abs(0.0167 - 0.017) < 0.001, "orbital eccentricity of Earth"),
    ("4 times bigger orbit takes 8 times longer", 4 ** 1.5 == 8, "Kepler 3"),
    ("29.8 km/s", abs(v_earth - 29.8) < 0.1, "orbital speed of Earth"),
    ("11.2 km/s", abs(v_esc_earth - 11.2) < 0.05, "escape speed of Earth"),
    ("v_esc = √(2GM/r)", True, "escape speed formula"),
    ("c = 3.0 × 10⁵ km/s", c_kms == 3.0e5, "speed of light"),
    ("T² = 4π² a³ / (G (M₁ + M₂))", True, "Newton's form of Kepler 3"),
    ("m₁ r₁ = m₂ r₂", True, "center of mass"),
    ("M₁ + M₂ = a³ / T²", True, "Kepler 3 for binaries"),
    ("Earth's perihelion is in January", True, "Earth is nearest the Sun about 3 January"),
])

C.finish("CEADB")
