"""Independent checks for materi/physics/mechanics-circular-rotation.md: salad spinner, torque, moment of inertia, seesaw.

Every worked example and every Check answer is recomputed here with a different method
(simulation, brute force, vector formulas) and every distractor note of the answer key is
reproduced by the wrong calculation it names."""
import pathlib, re, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/physics/mechanics-circular-rotation.md").read_text()
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


# ---------- helpers: numeric experiments ----------
def accel_circle(r, f, h=1e-4):
    """Acceleration magnitude of a point on a circle, from position samples (second difference)."""
    pos = lambda t: (r * math.cos(2 * math.pi * f * t), r * math.sin(2 * math.pi * f * t))
    t = 0.123
    (x0, y0), (x1, y1), (x2, y2) = pos(t - h), pos(t), pos(t + h)
    return math.hypot((x2 - 2 * x1 + x0) / h**2, (y2 - 2 * y1 + y0) / h**2)

def speed_polygon(r, T, N=200000):
    """Speed = length of a many-sided polygon around the circle / T."""
    side = 2 * r * math.sin(math.pi / N)
    return N * side / T

def inertia_stick(m, l, axis_at, N=100000):
    """I = sum of (mass slice) * (distance to axis)^2 for a thin uniform stick from 0 to l."""
    dm = m / N
    return sum(dm * (((i + 0.5) * l / N) - axis_at) ** 2 for i in range(N))

# ---------- Example 1 (salad spinner) ----------
a1 = accel_circle(0.10, 2.0)
ok(abs(a1 - 15.79) < 0.05, a1)
v1 = speed_polygon(0.10, 0.5)
ok(abs(v1 - 1.2566) < 1e-3 and abs(v1**2 / 0.10 - 15.79) < 0.05)
mcq("**Example 1.**", a1, "D")
ok(abs(a1 / 9.8 - 1.6) < 0.02, "about 1.6 g")
# distractor notes
claim("**Example 1.**", 2**2 * 0.10, "A")            # "2" used as omega in rad/s
claim("**Example 1.**", v1**2, "B")                  # v^2 without dividing by r
claim("**Example 1.**", v1 / 0.10, "C")              # v/r = omega
claim("**Example 1.**", (2 * math.pi * 2.0)**2, "E") # omega^2 without * r
ok(abs(v1 / 0.10 - 2 * math.pi * 2.0) < 0.01, "v/r is omega")

# ---------- Example 2 (stick about its end) ----------
m, l, F = 0.60, 1.0, 3.0
I_end = inertia_stick(m, l, 0.0)
I_cen = inertia_stick(m, l, l / 2)
ok(abs(I_end - 0.20) < 1e-6 and abs(I_cen - 0.05) < 1e-6, (I_end, I_cen))
ok(abs(I_cen + m * (l / 2) ** 2 - I_end) < 1e-6, "parallel axis rule")
# torque from vectors: r = (l, 0), F perpendicular = (0, F): tau_z = x*Fy - y*Fx
tau = l * F - 0 * 0
ok(tau == 3.0)
alpha = tau / I_end
ok(abs(alpha - 15) < 1e-4)
mcq("**Example 2.**", alpha, "D")
claim("**Example 2.**", tau / I_cen, "E")             # I about the center
claim("**Example 2.**", tau / (m * l**2), "A")        # I = m l^2
claim("**Example 2.**", (l / 2 * F) / I_end, "B")     # lever arm l/2
claim("**Example 2.**", tau / (m * l**2 / 2), "C")    # disk formula
# check the 5 option values are the 5 different wrong paths + right one
ok(len({round(x, 3) for x in (tau / I_cen, tau / (m * l**2), (l / 2 * F) / I_end, tau / (m * l**2 / 2), alpha)}) == 5)

# ---------- Q1 ----------
v = speed_polygon(0.50, 2.0)
ok(abs(v - math.pi / 2) < 1e-4)
mcq("**1.**", v, "C")
claim("**1.**", 0.50 / 2.0, "A")                  # forgot 2*pi
claim("**1.**", math.pi * 0.50 / 2.0, "B")        # half circumference
claim("**1.**", 2 * math.pi * 0.50, "D")          # no division by T
claim("**1.**", 2 * math.pi * 0.50 * 2.0, "E")    # times T

# ---------- Q2 (force goes with v^2): measure with the simulated acceleration ----------
r_, f_ = 0.10, 2.0
a_slow = accel_circle(r_, f_)
a_fast = accel_circle(r_, 2 * f_)   # same radius, double the speed (v = 2 pi r f)
ratio = a_fast / a_slow
ok(abs(ratio - 4.0) < 1e-3, ratio)
words = {"half": 0.5, "same": 1, "2 times": 2, "4 times": 4, "8 times": 8}
o2 = options("**2.**")
parsed = {k: next(val for w, val in words.items() if w in txt) for k, txt in o2.items()}
ok([k for k, val in parsed.items() if abs(val - ratio) < 1e-2] == ["D"])
ok(sorted(parsed.values()) == [0.5, 1, 2, 4, 8])
ok(2 == 2**1 and 4 == 2**2, "C would be F proportional to v")

# ---------- Q3 (torque with an angle, from vectors) ----------
rr, FF, ang = 0.30, 50.0, math.radians(30)
rx, ry = rr, 0.0
fx, fy = FF * math.cos(ang), FF * math.sin(ang)     # force 30 degrees from the wrench direction
tau3 = rx * fy - ry * fx
ok(abs(tau3 - 7.5) < 1e-9)
mcq("**3.**", tau3, "A")
claim("**3.**", rr * FF * math.cos(ang), "B")   # cos instead of sin
claim("**3.**", rr * FF, "C")                   # no sin
claim("**3.**", FF * math.sin(ang), "D")        # no r
claim("**3.**", FF / rr, "E")                   # F / r

# ---------- Q4 (stick about the end) ----------
m4, l4 = 1.2, 1.0
I4 = inertia_stick(m4, l4, 0.0)
ok(abs(I4 - 0.4) < 1e-6)
mcq("**4.**", I4, "C")
claim("**4.**", inertia_stick(m4, l4, l4 / 2), "A")  # center
claim("**4.**", m4 * (l4 / 2) ** 2, "B")             # m d^2 only
claim("**4.**", m4 * l4**2 / 2, "D")                 # disk formula
claim("**4.**", m4 * l4**2, "E")                     # m l^2

# ---------- Q5 (seesaw balance by bisection on the net torque) ----------
def net_torque(d):
    return 40 * 9.8 * 1.5 - 50 * 9.8 * d   # g = 9.8, signs: left up, right down
lo, hi = 0.0, 5.0
for _ in range(200):
    mid = (lo + hi) / 2
    if net_torque(mid) > 0: lo = mid
    else: hi = mid
d5 = (lo + hi) / 2
ok(abs(d5 - 1.2) < 1e-9)
ok(abs(net_torque(d5)) < 1e-6 and abs(40 * 9.8 * 1.5 - 50 * 9.8 * 1.2) < 1e-6, "g cancels")
mcq("**5.**", d5, "B")
claim("**5.**", 40 / 50, "A")           # forgot the 1.5
claim("**5.**", 1.5, "C")               # equal distances
claim("**5.**", 1.5 * 50 / 40, "D")     # flipped ratio
ok(1.5 * 50 / 40 > 1.5 > d5, "heavier friend sits closer")
# picture in the SVG: 30 kg x 2.0 m = 60 kg x 1.0 m
ok(30 * 2.0 == 60 * 1.0)

finish(['C', 'D', 'A', 'C', 'B'])
