"""Independent checks for materi/physics/mechanics-kinematics.md (examples + check questions)."""
import math, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/physics/mechanics-kinematics.md").read_text()
KEY = TXT.split("<details>")[1]
g = 9.8
n = 0


def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1


def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    return dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))


def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", KEY, re.M).group(1)


def num(s):
    return float(re.match(r"-?\d+(?:\.\d+)?", s.replace("−", "-")).group(0))


def letter_of(label, value, tol=0.0, conv=num):
    """letter of the single option whose value matches"""
    o = options(label)
    ok(len(set(o.values())) == 5, "options distinct")
    hits = [k for k, v in o.items() if abs(conv(v) - value) <= tol]
    ok(len(hits) == 1, f"{label}: hits {hits} for {value}")
    return hits[0]


# ---------- hook: lap in a 25 m pool
ok(25 + 25 == 50 and 25 - 25 == 0 and 50 / 40 == 1.25)

# ---------- Example 1: dash, integrate step by step
v0, v1, T = 4.0, 10.0, 1.5
a = (v1 - v0) / T
dt, t, x, v = 1e-5, 0.0, 0.0, v0
while t < T - 1e-12:
    x += v * dt + 0.5 * a * dt * dt
    v += a * dt
    t += dt
ok(abs(x - 10.5) < 1e-3 and abs(v - 10) < 1e-3, x)
ok(letter_of("**Example 1.**", x, 0.01) == "C")
ok(abs(a - 4.0) < 1e-9 and abs(a * T + 0.5 * a * T**2 - 10.5) < 1e-9)
# distractor claims
ok(abs(v0 * T - 6.0) < 1e-9 and letter_of("**Example 1.**", v0 * T) == "A")
ok(abs(v1 * T - 15) < 1e-9 and letter_of("**Example 1.**", v1 * T) == "D")
ok(abs((v0 + v1) * T - 21) < 1e-9 and letter_of("**Example 1.**", (v0 + v1) * T) == "E")
ok(abs((v1 - v0) * T - 9.0) < 1e-9 and letter_of("**Example 1.**", (v1 - v0) * T) == "B")

# ---------- Example 2: diver, Euler simulation of a projectile
h, vx0 = 4.9, 2.0
dt = 1e-6
x_, y_, vx, vy, t = 0.0, h, vx0, 0.0, 0.0
while y_ > 0:
    vy += g * dt
    y_ -= vy * dt
    x_ += vx * dt
    t += dt
speed = math.hypot(vx, vy)
ok(abs(t - 1.0) < 1e-3 and abs(vy - 9.8) < 1e-2, (t, vy))
ok(abs(speed - 10.0) < 0.01, speed)
ok(letter_of("**Example 2.**", speed, 0.05) == "D")
ok(abs(math.sqrt(vx0**2 + (g * 1.0) ** 2) - 10.002) < 0.01)
ok(letter_of("**Example 2.**", vx0) == "A" and letter_of("**Example 2.**", vy, 0.05) == "C")
ok(letter_of("**Example 2.**", 9.8 - 2.0, 0.05) == "B")
ok(letter_of("**Example 2.**", 9.8 + 2.0, 0.25) == "E")

# ---------- Q1: walk 5 east, 12 north
E, N = 5, 12
dist = E + N
disp = math.hypot(E, N)
ok(dist == 17 and abs(disp - 13) < 1e-12)
pair = lambda s: tuple(float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)[:2])
o = options("**1.**")
hits = [k for k, v in o.items() if pair(v) == (dist, disp)]
ok(hits == ["C"] and key_letter(1) == "C", hits)
ok([k for k, v in o.items() if pair(v) == (disp, dist)] == ["A"])      # swapped
ok([k for k, v in o.items() if pair(v) == (dist, dist)] == ["D"])      # displacement = path
ok([k for k, v in o.items() if pair(v) == (dist, N - E)] == ["E"])     # subtracted legs

# ---------- Q2: scooter, integrate v(t)
dt, t, x, v = 1e-4, 0.0, 0.0, 0.0
while t < 10 - 1e-9:
    acc = 12 / 4.0 if t < 4.0 - 1e-9 else 0.0
    x += (v + 0.5 * acc * dt) * dt
    v += acc * dt
    t += dt
ok(abs(x - 96) < 0.05, x)
ok(letter_of("**2.**", x, 0.1) == "D" and key_letter(2) == "D")
ok(letter_of("**2.**", 0.5 * 4 * 12) == "A")          # triangle only
ok(letter_of("**2.**", 12 * 4) == "B")                # speeding part as rectangle
ok(letter_of("**2.**", 12 * 6) == "C")                # steady part only
ok(letter_of("**2.**", 12 * 10) == "E")               # top speed all the time

# ---------- Q3: spoon, simulate the fall until the speed reaches 4.0 m/s
dt, v, y, t = 1e-6, 0.0, 0.0, 0.0
while v < 4.0:
    v += g * dt
    y += v * dt
    t += dt
ok(abs(y - 0.8163) < 1e-3 and abs(t - 4 / 9.8) < 1e-3, (y, t))
ok(letter_of("**3.**", y, 0.005) == "B" and key_letter(3) == "B")
ok(letter_of("**3.**", t, 0.005) == "A")                      # fall time in s
ok(letter_of("**3.**", 16 / g, 0.05) == "C")                  # v^2/g
ok(letter_of("**3.**", 0.5 * g * t, 0.05) == "D")             # 1/2 g t (t not squared)
ok(letter_of("**3.**", 16 / 2, 0.05) == "E")                  # v^2/2

# ---------- Q4: brake from 12 m/s; which candidate a stops in 36 m?
def stop_dist(a, v0=12.0):
    dt, x, v = 1e-4, 0.0, v0
    while v > 0:
        x += v * dt - 0.5 * a * dt * dt
        v -= a * dt
    return x

o = options("**4.**")
cands = {k: num(v) for k, v in o.items()}
good = [k for k, a_ in cands.items() if abs(stop_dist(a_) - 36) < 0.1]
ok(good == ["A"] and key_letter(4) == "A", good)
ok(cands["A"] == 2.0 and abs(stop_dist(2.0) - 36) < 0.1)
ok(36 / 12 == cands["B"] and 12**2 / 36 == cands["C"] and 12 / 2 == cands["D"] and cands["E"] == 12.0)
ok(abs(12 / 2.0 - 6.0) < 1e-9)  # time to stop = 6 s, and average speed = 6 m/s
ok(abs(0.5 * 12 * (12 / 2.0) - 36) < 1e-9)

# ---------- Q5: dropped vs thrown ball, simulate several throws
def land(vx0, h=20.0):
    dt, x, y, vx, vy, t, path = 1e-5, 0.0, h, vx0, 0.0, 0.0, 0.0
    while y > 0:
        vy += g * dt
        dx, dy = vx * dt, vy * dt
        x += dx; y -= dy; t += dt; path += math.hypot(dx, dy)
    return t, path, math.hypot(vx, vy)

t_drop, path_drop, sp_drop = land(0.0)
times = []
for vx0 in (1, 5, 10, 25):
    t_, path_, sp_ = land(vx0)
    times.append(t_)
    ok(abs(t_ - t_drop) < 1e-3, "same landing time")
    ok(path_ > path_drop and sp_ > sp_drop)   # longer path, bigger landing speed
ok(max(times) - min(times) < 1e-3)           # (D) "depends on the throw" is false
ok(options("**5.**")["E"].startswith("They land at the same time") and key_letter(5) == "E")
ok(sorted(key_letter(q) for q in range(1, 6)) == ["A", "B", "C", "D", "E"])
print(f"OK {n} checks")
