"""Independent checks for materi/physics/mechanics-gravity.md: gravitation, g, orbits.

Every worked example and every Check answer is recomputed here with a different method
(simulation, brute force, vector formulas) and every distractor note of the answer key is
reproduced by the wrong calculation it names."""
import pathlib, re, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/physics/mechanics-gravity.md").read_text()
n = 0
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1


def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    return dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))


def first_number(s):
    s = re.sub(r"\s*×\s*10", "e", s.replace("−", "-")).translate(SUP)
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s)
    m = re.search(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", s)
    return m.group(0)


def matches(opt_text, value):
    """True if value rounds to the number printed in the option (same number of decimals)."""
    tok = first_number(opt_text)
    mant = tok.split("e")[0]
    exp = int(tok.split("e")[1]) if "e" in tok else 0
    dec = len(mant.split(".")[1]) if "." in mant else 0
    scale = 10 ** exp
    return abs(value / scale - float(mant)) <= 0.5 * 10 ** (-dec) + 1e-9


def letters(label, value):
    o = options(label)
    return [k for k, v in o.items() if matches(v, value)]


def mcq(label, value, key):
    o = options(label)
    ok(len(set(o.values())) == 5, "options distinct")
    ok(letters(label, value) == [key], f"{label}: {letters(label, value)} vs {key} for {value}")


def claim(label, value, letter):
    """A distractor note in the key: this wrong path must give exactly that option."""
    ok(letters(label, value) == [letter], f"{label} claim {letter}: got {letters(label, value)} for {value}")


def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", TXT.split("<details>")[1], re.M).group(1)


def finish(keys):
    got = [key_letter(q) for q in range(1, 6)]
    ok(got == keys, f"keys {got} vs {keys}")
    ok(max(got.count(c) for c in "ABCDE") <= 2, "a letter is used more than twice")
    print(f"OK {n} checks")


G = 6.674e-11
g0 = 9.8

def grav_force(m1, m2, r):
    return G * m1 * m2 / r**2

def orbit_sim(GM, r0, v0, t_end, dt=1e-3):
    """Leapfrog integration of an orbit around a fixed mass at the origin (units are arbitrary but consistent).
    Returns (min radius, max radius, speed at the end)."""
    x, y, vx, vy = r0, 0.0, 0.0, v0
    rmin = rmax = r0
    t = 0.0
    def acc(x, y):
        r3 = (x * x + y * y) ** 1.5
        return -GM * x / r3, -GM * y / r3
    ax, ay = acc(x, y)
    while t < t_end:
        vx += 0.5 * dt * ax; vy += 0.5 * dt * ay
        x += dt * vx; y += dt * vy
        ax, ay = acc(x, y)
        vx += 0.5 * dt * ax; vy += 0.5 * dt * ay
        t += dt
        r = math.hypot(x, y)
        rmin, rmax = min(rmin, r), max(rmax, r)
    return rmin, rmax, math.hypot(vx, vy)

# ---------- hook + core-idea facts ----------
M_e, R_e = 5.97e24, 6.371e6
M_m, R_m = 7.342e22, 1.737e6
M_mars, R_mars = 6.417e23, 3.3895e6
gE, gM, gMars = G * M_e / R_e**2, G * M_m / R_m**2, G * M_mars / R_mars**2
ok(abs(gE - 9.8) < 0.05 and abs(gM - 1.6) < 0.05 and abs(gMars - 3.7) < 0.05, (gE, gM, gMars))
ok(5.0 < g0 / gM < 6.5, "Moon jump about 6 times higher: h = v^2/(2g)")
ok(abs(60 * g0 - 588) < 1e-9 and round(60 * 3.72) == 223 and round(60 * 1.62) == 97, "weights in the picture")
iss = (R_e / (R_e + 4.0e5)) ** 2
ok(0.85 < iss < 0.92, iss)     # about 90 % at the ISS height
for k, gg in ((1, 9.8), (2, 2.45), (3, 1.09), (4, 0.61)):
    ok(abs(g0 / k**2 - gg) < 0.006, (k, g0 / k**2))      # numbers in the weight picture
for fac, expect in ((2, 1/4), (3, 1/9), (0.5, 4)):
    ok(abs(grav_force(1, 1, 1.0 * fac) / grav_force(1, 1, 1.0) - expect) < 1e-12)
ok(abs(grav_force(2, 1, 1) / grav_force(1, 1, 1) - 2) < 1e-12 and abs(grav_force(2, 2, 1) / grav_force(1, 1, 1) - 4) < 1e-12)

# ---------- Example 1 ----------
R = 6400.0     # km
lo, hi = R, 10 * R     # r from the center; find r where g falls to a quarter
for _ in range(100):
    mid = (lo + hi) / 2
    if (R / mid) ** 2 > 0.25: lo = mid
    else: hi = mid
r1 = (lo + hi) / 2
h1 = r1 - R
ok(abs(h1 - 6400) < 1e-6, h1)
mcq("**Example 1.**", h1, "C")
claim("**Example 1.**", R / 4, "A")          # divided the radius by 4
claim("**Example 1.**", R / 2, "B")          # divided by 2
claim("**Example 1.**", 2 * R, "D")          # r instead of h
# if g were proportional to 1/r: quarter at r = 4R, h = 3R
claim("**Example 1.**", 4 * R - R, "E")
ok(abs(g0 * (R / (2 * R)) ** 2 - 2.45) < 1e-12)

# ---------- Example 2 ----------
gX = G * (2 * M_e) / (2 * R_e) ** 2
ratio = gX / (G * M_e / R_e**2)
ok(abs(ratio - 0.5) < 1e-12)
W2 = 50 * g0 * ratio
ok(abs(W2 - 245) < 1e-9 and abs(50 * g0 - 490) < 1e-9)
mcq("**Example 2.**", W2, "B")
claim("**Example 2.**", 490 / 4, "A")        # only the radius (quarter)  [122.5 shown as 123]
claim("**Example 2.**", 490 * 2, "D")        # only the mass
claim("**Example 2.**", 490 * 2**2, "E")     # R^2 on the top, mass forgotten
ok(abs(50 * (G * 2 * M_e / (2 * R_e)**2) / (G * M_e / R_e**2) / 50 - 0.5) < 1e-12, "mass of the player is unchanged: 50 kg")

# ---------- Q1 ----------
ok(abs(grav_force(7, 9, 2.0) / grav_force(7, 9, 1.0) - 0.25) < 1e-12)
mcq_text = {"A": 4, "B": 2, "C": 1, "D": 0.25, "E": 0.125}
o = options("**1.**")
words = {"4 times": 4, "2 times": 2, "same": 1, "¼": 0.25, "⅛": 0.125}
parsed = {k: next(v for w, v in words.items() if w in t) for k, t in o.items()}
ok([k for k, v in parsed.items() if abs(v - 0.25) < 1e-12] == ["D"] and len(set(parsed.values())) == 5)
ok(abs(0.5**3 - 0.125) < 1e-12)

# ---------- Q2 ----------
F2 = grav_force(2.0, 3.0, 0.50)
ok(abs(F2 - 1.602e-9) < 1e-12, F2)
mcq("**2.**", F2, "C")
claim("**2.**", G * 2.0 * 3.0 / 0.50, "A")          # r not squared
claim("**2.**", G * (2.0 + 3.0) / 0.50**2, "B")     # masses added
claim("**2.**", G * 2.0 * 3.0 / 0.25**2, "D")       # squared 0.25
claim("**2.**", 2.0 * 3.0 / 0.50**2, "E")           # no G

# ---------- Q3 ----------
g3 = G * M_e / (R_e / 2) ** 2
ok(abs(g3 / gE - 4) < 1e-12)
v3 = 4 * g0
mcq("**3.**", v3, "E")
claim("**3.**", g0 / 4, "A")
claim("**3.**", g0 / 2, "B")
claim("**3.**", g0, "C")
claim("**3.**", g0 * 2, "D")

# ---------- Q4 (orbit simulation, units with GM = 1) ----------
GMu = 1.0
vA = math.sqrt(GMu / 1.0)
vB = math.sqrt(GMu / 4.0)
ok(abs(vB / vA - 0.5) < 1e-12)
for r0, v0 in ((1.0, vA), (4.0, vB)):
    rmin, rmax, vend = orbit_sim(GMu, r0, v0, 2 * math.pi * r0 / v0 * 1.0, dt=2e-3)
    ok(rmax / rmin < 1.0005, (r0, rmin, rmax))      # the circle really is a circle
    ok(abs(vend - v0) / v0 < 5e-4)
# a faster launch from r0=1 is NOT circular
rmin, rmax, _ = orbit_sim(GMu, 1.0, 1.2, 8.0, dt=2e-3)
ok(rmax / rmin > 1.3)
# the mass of the satellite does not matter: m cancels in G M m / r^2 = m v^2 / r
for msat in (1.0, 1000.0):
    Fg = GMu * msat / 4.0**2
    ok(abs(math.sqrt(Fg * 4.0 / msat) - vB) < 1e-12)   # m v^2 / r = F  ->  v = sqrt(F r / m)
mcq_words = {"A": 0.25, "B": 0.5, "C": 1.0, "D": 2.0, "E": 4.0}
o = options("**4.**")
words = {"¼": 0.25, "½": 0.5, "same": 1.0, "2 times": 2.0, "4 times": 4.0}
parsed = {k: next(v for w, v in words.items() if w in t) for k, t in o.items()}
ok(parsed == mcq_words)
ok([k for k, v in parsed.items() if abs(v - vB / vA) < 1e-12] == ["B"])
ok(math.sqrt(4) == 2 and 1 / 4 == 0.25)       # A: v ~ 1/r gives 1/4 ; D/E: farther = faster

# ---------- Q5 ----------
W0, g_old, g_new = 686.0, 9.8, 3.5
m5 = W0 / g_old
ok(abs(m5 - 70) < 1e-9)
W5 = m5 * g_new
ok(abs(W5 - 245) < 1e-9)
def pair(t): return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)][:2]
o = options("**5.**")
ok([k for k, t in o.items() if pair(t) == [round(m5), round(W5)]] == ["A"])
ok(pair(o["B"]) == [round(m5 * g_new / g_old), 245])        # mass scaled with g
ok(pair(o["C"]) == [70, 686])                               # old weight kept
ok(pair(o["D"]) == [round(W0 / g_new), 686])                # old weight / new g
ok(pair(o["E"]) == [round(W0 / g_new), 245])
ok(abs(m5 * g_new / g_old - 25) < 1e-9 and abs(W0 / g_new - 196) < 1e-9)

finish(['D', 'C', 'E', 'B', 'A'])
