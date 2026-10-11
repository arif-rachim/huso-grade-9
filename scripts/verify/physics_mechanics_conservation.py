"""Independent checks for materi/physics/mechanics-conservation.md (examples + check questions)."""
import math, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/physics/mechanics-conservation.md").read_text()
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


def throw_speed(v0, h, angle_deg, dt=2e-5):
    """step-by-step projectile; returns the speed when it reaches the ground"""
    a = math.radians(angle_deg)
    vx, vy, y = v0 * math.cos(a), v0 * math.sin(a), h
    while y > 0:
        vy -= g * dt
        y += vy * dt
    return math.hypot(vx, vy)


# ---------- hook: orb at 10 m/s from 4.9 m, many angles, same landing speed
speeds = [throw_speed(10.0, 4.9, a) for a in (-90, -30, 0, 45, 90)]
ok(max(speeds) - min(speeds) < 0.01 and abs(speeds[0] - 14.0) < 0.02, speeds)

# ---------- Example 1: slide energies
m, h, v = 40.0, 4.9, 8.0
pe, ke = m * g * h, 0.5 * m * v * v
ok(abs(pe - 1920.8) < 1e-9 and ke == 1280.0)
lost = pe - ke
ok(abs(lost - 640.8) < 1e-9 and letter_of("**Example 1.**", lost, 1.0) == "A")
ok(letter_of("**Example 1.**", ke) == "B" and letter_of("**Example 1.**", pe, 1.0) == "C")
ok(letter_of("**Example 1.**", pe + ke, 1.0) == "D" and letter_of("**Example 1.**", 0) == "E")
# step-by-step down a smooth slide (no friction) would give v = sqrt(2gh) = 9.8 m/s > 8.0 m/s
ok(abs(math.sqrt(2 * g * h) - 9.8) < 0.005 and 8.0 < math.sqrt(2 * g * h))

# ---------- Example 2: sticking trays, brute-force the common speed from momentum
m1, u1, m2 = 3.0, 4.0, 1.0
cand = [i / 1000 for i in range(0, 8001)]
vf = min(cand, key=lambda w: abs(m1 * u1 - (m1 + m2) * w))
ok(abs(vf - 3.0) < 1e-9)
ke0 = 0.5 * m1 * u1**2
ke1 = 0.5 * (m1 + m2) * vf**2
ok(ke0 == 24.0 and ke1 == 18.0 and ke0 - ke1 == 6.0)
ok(letter_of("**Example 2.**", ke0 - ke1) == "B")
ok(letter_of("**Example 2.**", 0) == "A" and letter_of("**Example 2.**", m1 * u1) == "C")   # p = 12 kg m/s as J
ok(letter_of("**Example 2.**", ke1) == "D" and letter_of("**Example 2.**", ke0) == "E")

# ---------- Q1: orb thrown at 8.0 m/s from 9.8 m
sp = [throw_speed(8.0, 9.8, a) for a in (-90, -45, 0, 30, 90)]
ok(max(sp) - min(sp) < 0.01 and abs(sp[0] - 16.0) < 0.02, sp)
ok(letter_of("**1.**", sp[0], 0.05) == "C" and key_letter(1) == "C")
ok(letter_of("**1.**", 8.0) == "A")
ok(letter_of("**1.**", math.sqrt(2 * g * 9.8), 0.15) == "B")          # forgot the initial speed
ok(letter_of("**1.**", 8.0 + math.sqrt(2 * g * 9.8), 0.15) == "D")    # added the speeds
ok(letter_of("**1.**", 8.0**2 + 2 * g * 9.8, 0.2) == "E")             # v^2, no square root

# ---------- Q2: work by integrating F . dx along the floor
F, ang, d = 50.0, math.radians(60), 10.0
steps = 100000
W = sum(F * math.cos(ang) * (d / steps) for _ in range(steps))        # Fx over each small dx
ok(abs(W - 250.0) < 1e-6)
ok(letter_of("**2.**", W, 1e-6) == "C" and key_letter(2) == "C")
ok(letter_of("**2.**", F * d, 1e-6) == "E")                                   # ignored the angle
ok(letter_of("**2.**", F * d * math.sin(ang), 0.5) == "D")             # used sin
ok(letter_of("**2.**", 0.5 * F * d * math.cos(ang), 1e-6) == "B")            # extra 1/2
ok(letter_of("**2.**", F * d * math.cos(math.radians(90)), 1e-9) == "A")

# ---------- Q3: elastic collision, search for the outcome that conserves BOTH p and KE
M1, U1, M2 = 3.0, 2.0, 1.0
sols = []
for i in range(-100, 401):
    w1 = i / 100
    for j in range(-100, 801):
        w2 = j / 100
        if abs(M1 * w1 + M2 * w2 - M1 * U1) < 1e-9 and abs(0.5 * M1 * w1**2 + 0.5 * M2 * w2**2 - 0.5 * M1 * U1**2) < 1e-9:
            sols.append((w1, w2))
ok(sorted(sols) == [(1.0, 3.0), (2.0, 0.0)], sols)       # (2,0) = "no collision"; (1,3) is the real one
ok(abs((3.0 - 1.0) - U1) < 1e-9)                            # separation speed = approach speed
ok(letter_of("**3.**", 3.0) == "D" and key_letter(3) == "D")
ok(letter_of("**3.**", 1.0) == "A")                                   # speed of the heavy cart afterward
ok(letter_of("**3.**", M1 * U1 / (M1 + M2)) == "B")                   # sticking speed 1.5
ok(letter_of("**3.**", U1) == "C" and letter_of("**3.**", M1 * U1) == "E")

# ---------- Q4: diver, L = I w constant
I0, w0 = 1.0, 0.80
L = I0 * w0
w1 = L / (I0 / 3)
ok(abs(w1 - 2.4) < 1e-12 and letter_of("**4.**", w1, 1e-9) == "A" and key_letter(4) == "A")
ok(letter_of("**4.**", w0 / 3, 0.005) == "B" and letter_of("**4.**", w0) == "C")
ok(letter_of("**4.**", w0 * math.sqrt(3), 0.02) == "D" and letter_of("**4.**", w0 * 9, 1e-9) == "E")
# energy check for a spinner: KE = L^2 / 2I rises by the factor 3 (work done by the diver)
ok(abs((L**2 / (2 * I0 / 3)) / (L**2 / (2 * I0)) - 3.0) < 1e-12)
# the skater in the picture: I 3.0 -> 1.0, w 2.0 -> 6.0, L = 6, KE 6 J -> 18 J
ok(3.0 * 2.0 == 1.0 * 6.0 == 6.0 and 0.5 * 3.0 * 2.0**2 == 6.0 and 0.5 * 1.0 * 6.0**2 == 18.0)

# ---------- Q5: lifting the flour at constant speed: work = integral of F dy, then P = W / t
mass, H, T = 20.0, 3.0, 6.0
steps = 60000
W = sum(mass * g * (H / steps) for _ in range(steps))                  # F = mg balances gravity
P = W / T
ok(abs(W - 588.0) < 1e-6 and abs(P - 98.0) < 1e-6)
ok(letter_of("**5.**", P, 1e-6) == "B" and key_letter(5) == "B")
ok(letter_of("**5.**", 0.5 * P, 1e-6) == "A")                                # extra 1/2
ok(letter_of("**5.**", mass * g * T / H, 1e-6) == "C")                       # swapped H and T
ok(letter_of("**5.**", W, 1e-6) == "D")                                      # work, forgot to divide by t
ok(letter_of("**5.**", W * T, 1e-6) == "E")                                  # multiplied by t
# picture numbers
ok(abs(2 * g * 5 - 98.0) < 1e-9 and abs(2 * g * 3 - 58.8) < 1e-9 and abs(98 - 58.8 - 39.2) < 1e-9)
ok(abs(0.5 * 2 * (1.0**2) + 0.5 * 1 * 4.0**2 - 9.0) < 1e-9 and 0.5 * 2 * 3.0**2 == 9.0 and 0.5 * 3 * 2.0**2 == 6.0)
ok(sorted(key_letter(q) for q in range(1, 6)) == ["A", "B", "C", "C", "D"])
print(f"OK {n} checks")
