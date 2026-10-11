"""Independent checks for materi/physics/mechanics-shm.md: spring and pendulum SHM.

Every worked example and every Check answer is recomputed here with a different method
(simulation, brute force, vector formulas) and every distractor note of the answer key is
reproduced by the wrong calculation it names."""
import pathlib, re, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/physics/mechanics-shm.md").read_text()
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


g = 9.8

def sim_spring(m, k, x0, t_end, dt=1e-5):
    """Velocity Verlet for F = -k x. Returns (peak speed, times of upward zero crossings, times of x maxima, trace of x at maxima/minima)."""
    x, v, t = x0, 0.0, 0.0
    a = -k * x / m
    vmax = 0.0
    maxima, minima = [], []
    prev_v = v
    while t < t_end:
        x += v * dt + 0.5 * a * dt * dt
        a_new = -k * x / m
        v_new = v + 0.5 * (a + a_new) * dt
        t += dt
        if prev_v > 0 >= v_new: maxima.append(t)   # x passes a maximum when v changes + to -
        if prev_v < 0 <= v_new: minima.append(t)
        prev_v = v_new
        v, a = v_new, a_new
        vmax = max(vmax, abs(v))
    return vmax, maxima, minima

def sim_pendulum_period(L, m, theta0, mg=g, dt=2e-4):
    """RK4 on m*L*theta'' = -m*g*sin(theta). Returns the period measured between two moments where theta' changes - to +."""
    th, w, t = theta0, 0.0, 0.0
    f = lambda th_, w_: (w_, -(mg / L) * math.sin(th_))   # the mass m cancels; kept as an argument on purpose
    turns = []
    prev_w = w
    while len(turns) < 2:
        k1 = f(th, w); k2 = f(th + dt/2*k1[0], w + dt/2*k1[1])
        k3 = f(th + dt/2*k2[0], w + dt/2*k2[1]); k4 = f(th + dt*k3[0], w + dt*k3[1])
        th += dt/6*(k1[0] + 2*k2[0] + 2*k3[0] + k4[0]); w += dt/6*(k1[1] + 2*k2[1] + 2*k3[1] + k4[1]); t += dt
        if prev_w < 0 <= w: turns.append(t)
        prev_w = w
    return turns[1] - turns[0]

# ---------- Example 1 ----------
m1, k1_, A1 = 0.50, 200.0, 0.10
vmax, maxima, minima = sim_spring(m1, k1_, A1, 1.0, dt=2e-5)
ok(abs(vmax - 2.0) < 1e-3, vmax)
mcq("**Example 1.**", vmax, "B")
ok(abs(0.5 * k1_ * A1**2 - 1.0) < 1e-12)
T1 = maxima[1] - maxima[0] if len(maxima) > 1 else None
ok(T1 is not None and abs(T1 - 2 * math.pi * math.sqrt(m1 / k1_)) < 2e-4 and abs(T1 - 0.314) < 1e-3, T1)
# same period for a half amplitude
v_half, max_half, _ = sim_spring(m1, k1_, 0.05, 1.0, dt=2e-5)
ok(abs((max_half[1] - max_half[0]) - T1) < 2e-4, "period independent of the amplitude")
claim("**Example 1.**", 0.5 * k1_ * A1**2, "A")        # energy in J
claim("**Example 1.**", k1_ * A1**2 / m1, "C")          # v^2, no root
claim("**Example 1.**", k1_ * A1, "D")                  # force
claim("**Example 1.**", k1_ * A1 / m1, "E")             # max acceleration
# the max acceleration really is kA/m at the end of the motion
ok(abs(k1_ * A1 / m1 - 40.0) < 1e-12)

# ---------- Example 2 ----------
T_target = 3.0
lo, hi = 0.1, 20.0
for _ in range(40):
    mid = (lo + hi) / 2
    if sim_pendulum_period(mid, 1.0, math.radians(2.0), dt=1e-3) < T_target: lo = mid
    else: hi = mid
L2 = (lo + hi) / 2
ok(abs(L2 - 2.234) < 0.01, L2)
mcq("**Example 2.**", L2, "B")
ok(abs(L2 - g * 9.0 / (4 * math.pi**2)) < 0.01)
claim("**Example 2.**", (T_target / (2 * math.pi))**2, "A")     # forgot g
claim("**Example 2.**", g * (T_target / (2 * math.pi)), "C")    # forgot to square T/2pi
claim("**Example 2.**", g * T_target**2 / (4 * math.pi), "D")   # 4 pi instead of 4 pi^2
claim("**Example 2.**", g * T_target**2, "E")                   # forgot 2 pi
# one-meter pendulum is the 2 s "tick-tock" pendulum
ok(abs(sim_pendulum_period(1.0, 1.0, math.radians(2.0), dt=1e-3) - 2.007) < 0.005)

# ---------- Q1 ----------
# count cycles of a wave in 60 s
cycles = sum(1 for i in range(1, 600000) if math.sin(2 * math.pi * (25 / 60) * (i - 1) / 10000) < 0 <= math.sin(2 * math.pi * (25 / 60) * i / 10000))
ok(cycles in (24, 25), cycles)   # the first rising crossing at t = 0 is not counted
f1 = 25 / 60
mcq("**1.**", f1, "A")
claim("**1.**", 60 / 25, "B")       # that is the period in seconds
claim("**1.**", 25, "C")
claim("**1.**", 25 * 60, "E")
ok(abs(1 / f1 - 2.4) < 1e-12)

# ---------- Q2 ----------
mass, x = 2.0, 0.050
# at rest the net force is zero: k*x - m*g = 0; find k by scanning for the k where the net force vanishes
lo, hi = 1.0, 10000.0
for _ in range(200):
    mid = (lo + hi) / 2
    if mid * x - mass * g < 0: lo = mid
    else: hi = mid
k2 = (lo + hi) / 2
ok(abs(k2 - 392) < 1e-6)
mcq("**2.**", k2, "D")
claim("**2.**", mass * g / 5.0, "A")      # 5.0 taken as meters
claim("**2.**", mass * g, "B")            # the weight
claim("**2.**", mass / x, "C")            # forgot g
claim("**2.**", mass * g / 0.0050, "E")   # 5.0 cm turned into 0.0050 m

# ---------- Q3 ----------
T_old = sim_pendulum_period(0.5, 1.0, math.radians(3.0), dt=1e-3)
T_new = sim_pendulum_period(0.5 * 4, 3.0, math.radians(3.0), dt=1e-3)     # 4 times L, 3 times the mass
ratio = T_new / T_old
ok(abs(ratio - 2.0) < 0.003, ratio)
mcq("**3.**", 1.5 * ratio, "B")
claim("**3.**", 1.5 * 4, "D")           # forgot the square root
claim("**3.**", 1.5 * 2 * 3, "E")       # multiplied by the mass factor too
claim("**3.**", 1.5 * 3, "C")           # only the mass factor
claim("**3.**", 1.5, "A")

# ---------- Q4 ----------
k4, m4 = 20.0, 0.5
_, maxima4, minima4 = sim_spring(m4, k4, 0.30, 4.0, dt=2e-5)
ok(maxima4 and minima4)
T4_sim = maxima4[1] - maxima4[0]
half = minima4[0]            # time from release (x = +A) to the first time the block stops at the far end
ok(abs(T4_sim - 2 * half) < 5e-4, (T4_sim, half))
T4 = 2 * 0.80
mcq("**4.**", T4, "D")
claim("**4.**", 0.80, "B")        # half cycle read as a full one
claim("**4.**", 0.80 / 2, "A")    # quarter cycle
claim("**4.**", 0.75 * T4, "C")   # three quarters
claim("**4.**", 2 * T4, "E")

# ---------- Q5 ----------
Lp, mb, h = 1.0, 0.50, 0.20
theta0 = math.acos(1 - h / Lp)
th, w, t, dt = theta0, 0.0, 0.0, 1e-5
f = lambda th_, w_: (w_, -(g / Lp) * math.sin(th_))
v_bottom = None
while th > 0:
    k1 = f(th, w); k2 = f(th + dt/2*k1[0], w + dt/2*k1[1]); k3 = f(th + dt/2*k2[0], w + dt/2*k2[1]); k4 = f(th + dt*k3[0], w + dt*k3[1])
    th += dt/6*(k1[0] + 2*k2[0] + 2*k3[0] + k4[0]); w += dt/6*(k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
v_bottom = abs(w) * Lp
ok(abs(v_bottom - math.sqrt(2 * g * h)) < 5e-3 and abs(v_bottom - 1.98) < 0.01, v_bottom)
mcq("**5.**", v_bottom, "C")
claim("**5.**", mb * g * h, "A")             # energy
claim("**5.**", math.sqrt(g * h), "B")       # forgot the 2
claim("**5.**", 2 * g * h, "D")              # no square root
claim("**5.**", g, "E")

finish(['A', 'D', 'B', 'D', 'C'])
