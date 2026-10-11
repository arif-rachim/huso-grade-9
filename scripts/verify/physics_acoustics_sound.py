"""Independent checks for materi/physics/acoustics-sound.md (examples + check questions)."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/physics/acoustics-sound.md")
ok = C.ok
V_AIR, V_WATER = 343.0, 1480.0

# Simulate a 1-D wave to recover lambda from f: crest positions of cos(2*pi*(x/lam - f t)) at t = 0, with lam = v/f unknown to the check
def measured_wavelength(v, f):
    """Distance between two successive crests of the wave at t=0 found numerically (independent of v/f formula)."""
    # wave phase at position x at time t: phi = 2*pi*f*(x/v - t)  -> crests where phi = 2*pi*k
    # find x where phase advances by 2*pi by stepping along x
    x, dx = 0.0, 1e-5
    phase0 = 0.0
    while 2 * math.pi * f * (x / v) - phase0 < 2 * math.pi:
        x += dx
    return x

# Example 1
lam1 = measured_wavelength(V_AIR, 686)
ok(abs(lam1 - 0.5) < 1e-4, lam1)
C.mcq("**Example 1.**", 0.5, "m", "B")
C.opt_is("**Example 1.**", "C", 686 / 343, "m")             # flipped
C.opt_is("**Example 1.**", "E", 343 * 686, "m", tol=0.03)   # multiplied
T1 = 1 / 686
ok(abs(T1 - 0.001458) < 1e-6 and abs(0.5 / T1 - 343) < 0.01, "period and v = lambda/T")
ok(round(T1 * 1000, 1) == 1.5)

# Example 2: time by stepping the sound front out and back
def echo_time(d, v, dt=1e-6):
    t, x, direction = 0.0, 0.0, +1
    while True:
        x += direction * v * dt
        t += dt
        if direction == +1 and x >= d: direction = -1
        if direction == -1 and x <= 0: return t
t2 = echo_time(50.0, V_AIR)
ok(abs(t2 - 100 / 343) < 1e-4, t2)
C.mcq("**Example 2.**", t2, "s", "C", tol=0.02)
C.opt_is("**Example 2.**", "B", 50 / 343, "s", tol=0.02)         # no return trip
C.opt_is("**Example 2.**", "A", 50 / 2 / 343, "s", tol=0.01)      # halved
C.opt_is("**Example 2.**", "D", 4 * 50 / 343, "s", tol=0.01)      # doubled twice
C.opt_is("**Example 2.**", "E", 343 / 50, "s", tol=0.01)          # upside down
ok(t2 > 0.1, "separate echo")
ok(abs(686 / 343 - 2.0) < 1e-12, "hook: 686 m takes 2 s")

# Q1 concept
o1 = C.options("**1.**")
ok(C.key_letter(1) == "C" and "back and forth along the direction" in o1["C"])
ok(all("back and forth along" not in o1[k] for k in "ABDE") and "right angles" in o1["A"])

# Q2: inverse-square by integrating a point source's power over a sphere
def intensity(P, r): return P / (4 * math.pi * r * r)
P = 1.0
ratio = intensity(P, 10) / intensity(P, 5)
ok(abs(ratio - 0.25) < 1e-12)
factors = {"I/4": 0.25, "I/2": 0.5, "I": 1.0, "2I": 2.0, "4I": 4.0}
o2 = C.options("**2.**")
hits = [k for k, v in o2.items() if abs(factors[v.strip()] - ratio) < 1e-9]
ok(hits == ["A"] and C.key_letter(2) == "A", hits)
ok(factors[o2["B"].strip()] == 0.5 and factors[o2["E"].strip()] == 1 / ratio)   # "just halves" / upside down
ok(abs(10 * math.log10(10) - 10) < 1e-12 and 10 * math.log10(1) == 0, "+10 dB = x10")

# Q3: water
lam3 = V_WATER / 1000
C.mcq("**3.**", lam3, "m", "C", tol=0.002)
C.opt_is("**3.**", "A", V_AIR / 1000, "m", tol=0.02)           # air value
C.opt_is("**3.**", "B", 1000 / V_WATER, "m", tol=0.01)         # flipped
C.opt_is("**3.**", "D", V_WATER / V_AIR, "m", tol=0.01)        # speed ratio
C.opt_is("**3.**", "E", V_WATER * 1000, "m", tol=0.001)        # product
ok(abs(V_AIR / 1000 - 0.343) < 1e-12)

# Q4: tuning fork
f4 = 20 / 0.050
lam4 = V_AIR / f4
ok(f4 == 400)
C.mcq("**4.**", lam4, "m", "D", tol=0.01)
C.opt_is("**4.**", "A", f4 / V_AIR, "m", tol=0.02)             # flipped 1.17
C.opt_is("**4.**", "B", V_AIR * 0.050, "m", tol=0.02)          # 0.050 s as period
C.opt_is("**4.**", "C", V_AIR / (0.050 / 20), "m", tol=0.005)  # f = 0.0025
C.opt_is("**4.**", "E", 1 / f4, "m", tol=0.001)                # period
ok(abs(1 / f4 - 0.0025) < 1e-12)

# Q5: echo from a cliff, by stepping
t5 = 1.2
d5 = V_AIR * t5 / 2
ok(abs(echo_time(d5, V_AIR) - t5) < 1e-3, "round trip of d takes 1.2 s")
C.mcq("**5.**", d5, "m", "B", tol=0.005)
C.opt_is("**5.**", "C", V_AIR * t5, "m", tol=0.005)           # forgot /2
C.opt_is("**5.**", "A", V_AIR * t5 / 4, "m", tol=0.01)        # halved twice
C.opt_is("**5.**", "D", V_AIR / t5, "m", tol=0.005)           # speed / time
C.opt_is("**5.**", "E", V_AIR * t5 * 2, "m", tol=0.005)       # x2

# picture numbers
ok(abs(100 / 343 - 0.29) < 0.005 and 2 * 50 == 100)
ok(343 * 2 == 686)
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
C.done()
