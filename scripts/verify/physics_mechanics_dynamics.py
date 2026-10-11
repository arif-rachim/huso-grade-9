"""Independent checks for materi/physics/mechanics-dynamics.md (examples + check questions)."""
import math, pathlib, re
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/physics/mechanics-dynamics.md").read_text()
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
    o = options(label)
    ok(len(set(o.values())) == 5, "options distinct")
    hits = [k for k, v in o.items() if abs(conv(v) - value) <= tol]
    ok(len(hits) == 1, f"{label}: hits {hits} for {value}")
    return hits[0]


# ---------- Example 1: pot on the counter, integrate with kinetic friction
m, F, mu_k = 5.0, 20.0, 0.20
dt, v, t = 1e-5, 0.0, 0.0
while t < 1.0 - 1e-12:
    N = m * g                              # no vertical acceleration => N = mg
    f = mu_k * N if v > 0 or F > mu_k * N else F
    v += (F - f) / m * dt
    t += dt
a = v / 1.0                                 # started from rest, 1 s
ok(abs(a - 2.04) < 1e-3, a)
ok(letter_of("**Example 1.**", a, 0.05) == "A")
ok(abs(mu_k * m * g - 9.8) < 1e-9 and abs(F - 9.8 - 10.2) < 1e-9)
ok(letter_of("**Example 1.**", F / m) == "C")                      # ignored friction
ok(letter_of("**Example 1.**", (F + mu_k * m * g) / m, 0.05) == "D")  # added friction
ok(letter_of("**Example 1.**", (F - mu_k * m) / m, 0.05) == "B")      # f = mu m, forgot g
ok(letter_of("**Example 1.**", F - mu_k * m * g, 0.25) == "E")       # net force in N

# ---------- Example 2: Atwood machine; brute-force the tension that makes both accelerations equal
m1, m2 = 3.0, 2.0
best = None
for i in range(0, 6001):
    T = i * 0.01
    a1 = g - T / m1            # heavier mass, down positive
    a2 = T / m2 - g            # lighter mass, up positive
    if best is None or abs(a1 - a2) < best[0]:
        best = (abs(a1 - a2), T, a1)
T = best[1]
ok(abs(T - 23.52) < 0.01 and abs(best[2] - 1.96) < 0.01, best)
# exact check with fractions (g = 49/5)
G = Fraction(49, 5)
a_ex = (Fraction(3) - 2) * G / 5
T_ex = 2 * (G + a_ex)
ok(a_ex == Fraction(196, 100) and abs(float(T_ex) - 23.52) < 1e-9)
ok(letter_of("**Example 2.**", T, 0.5) == "C")
ok(letter_of("**Example 2.**", m2 * g, 0.5) == "B")                # lighter weight 19.6
ok(letter_of("**Example 2.**", m1 * g, 0.5) == "D")                # heavier weight 29.4
ok(letter_of("**Example 2.**", (m1 + m2) * g, 0.5) == "E")         # total weight 49
ok(letter_of("**Example 2.**", a_ex, 0.05) == "A")                 # the acceleration number 1.96
ok(T > m2 * g and T < m1 * g)                                      # tension must lie between the two weights

# ---------- Q1: Newton 3 in a contact model: you (60 kg) and a huge wall, repelling contact spring
M_wall, M_you, kc = 1e9, 60.0, 5e4
xw, xy, vw, vy = 0.0, -0.01, 0.0, 0.0     # you start 1 cm "inside" the contact layer, wall at x = 0
dt = 1e-5
F_wall_on_you, F_you_on_wall = [], []
for step in range(20000):
    overlap = xw - xy                     # you are on the +x side of the wall; overlap > 0 means in contact
    if overlap <= 0:
        break
    Fs = kc * overlap
    f_on_you, f_on_wall = +Fs, -Fs        # wall pushes you away (+x); you push the wall the other way
    F_wall_on_you.append(f_on_you); F_you_on_wall.append(f_on_wall)
    vy += f_on_you / M_you * dt;  xy += vy * dt
    vw += f_on_wall / M_wall * dt; xw += vw * dt
ok(len(F_wall_on_you) > 100)
ok(all(abs(a_ + b_) < 1e-9 for a_, b_ in zip(F_wall_on_you, F_you_on_wall)))   # equal and opposite at every step
ok(max(F_wall_on_you) > 0 and vy > 0)                                           # it pushes you away from the wall
ok(abs(vy) > 1e6 * abs(vw))                                                     # you move, the wall hardly does
ok(options("**1.**")["C"].startswith("Exactly 200 N, in the opposite") and key_letter(1) == "C")

# ---------- Q2: Moon
mass, gm = 49.0, 1.6
w_moon, w_earth = mass * gm, mass * g
ok(abs(w_moon - 78.4) < 1e-9 and abs(w_earth - 480.2) < 1e-9)
o = options("**2.**")
pr = lambda s: tuple(float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)[:2])
ok([k for k, v in o.items() if pr(v) == (49.0, 78.0)] == ["A"] and key_letter(2) == "A")
ok([k for k, v in o.items() if pr(v) == (49.0, 480.0)] == ["B"])
shrunk = mass * gm / g
ok(abs(shrunk - 8.0) < 1e-9 and [k for k, v in o.items() if pr(v) == (8.0, 78.0)] == ["C"])

# ---------- Q3: ramp, simulate 1 s of sliding with the vector gravity and a constraint to the slope
th, m3 = math.radians(30), 2.0
ux, uy = math.cos(th), math.sin(th)            # unit vector along the ramp (up the slope)
gx, gy = 0.0, -g
a_down = -(gx * ux + gy * uy)                  # acceleration down the slope = -(g . u), u = unit vector up the slope
ok(abs(a_down - 4.9) < 1e-9)
# energy check: slide s = 1 m along the ramp; the drop is s*sin(30 deg)
s_ = 1.0
v2 = 2 * g * (s_ * math.sin(th))
ok(abs(v2 / (2 * s_) - 4.9) < 1e-9)            # a = v^2 / 2s
Fnet = m3 * a_down
ok(abs(Fnet - 9.8) < 1e-9 and letter_of("**3.**", Fnet, 1e-6) == "B" and key_letter(3) == "B")
ok(letter_of("**3.**", a_down, 1e-6) == "A")                                   # the acceleration
ok(letter_of("**3.**", m3 * g * math.cos(th), 0.05) == "C")              # mg cos
ok(letter_of("**3.**", m3 * g, 0.5) == "D")                              # whole weight
ok(letter_of("**3.**", m3 * g / math.sin(th), 0.5) == "E")               # divided by sin

# ---------- Q4: sack of flour, model with static + kinetic friction
def run(push, mu_s=0.5, mu_k=0.4, m=10.0, T=2.0):
    N = m * g
    v, x, t, dt = 0.0, 0.0, 0.0, 1e-4
    f_first = None
    while t < T:
        if v == 0.0 and push <= mu_s * N:
            f = push                      # static friction balances the push
            acc = 0.0
        else:
            f = mu_k * N
            acc = (push - f) / m
        if f_first is None:
            f_first = f
        v += acc * dt
        x += v * dt
        t += dt
    return f_first, x, v

f40, x40, v40 = run(40.0)
ok(f40 == 40.0 and x40 == 0.0 and v40 == 0.0)              # does not move; friction = push
ok(letter_of("**4.**", f40) == "C" and key_letter(4) == "C")
f50, x50, v50 = run(50.0)
ok(x50 > 0.1 and abs(v50 - (50 - 39.2) / 10 * 2.0) < 0.01)  # 50 N pushes it over the 49 N limit
ok(letter_of("**4.**", 0.4 * 98, 0.5) == "B")             # kinetic value used wrongly
ok(letter_of("**4.**", 0.5 * 98) == "D" and letter_of("**4.**", 98) == "E" and letter_of("**4.**", 0) == "A")

# ---------- Q5: elevator, get the person's acceleration from positions (finite differences)
mp, a_el = 60.0, 2.0
dt = 1e-3
pos = [0.5 * a_el * (i * dt) ** 2 for i in range(0, 2001)]            # elevator (and person) height
acc = (pos[1001] - 2 * pos[1000] + pos[999]) / dt**2
ok(abs(acc - 2.0) < 1e-3)
N_scale = mp * g + mp * acc                                             # N - mg = ma
ok(abs(N_scale - 708) < 0.1)
ok(letter_of("**5.**", N_scale, 0.5) == "D" and key_letter(5) == "D")
ok(letter_of("**5.**", mp * (g - a_el), 0.5) == "B")                   # elevator speeding up downward
ok(letter_of("**5.**", mp * g, 0.5) == "C")
ok(letter_of("**5.**", mp * a_el) == "A")
ok(letter_of("**5.**", mp * g * a_el, 5) == "E")                        # 1176 ~ 1180
ok(sorted(key_letter(q) for q in range(1, 6)) == ["A", "B", "C", "C", "D"])
print(f"OK {n} checks")
