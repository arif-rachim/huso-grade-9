"""Independent checks for materi/chemistry/physical-equilibrium.md.
Method: ICE tables solved by brute-force time stepping of the rate laws, K from DeltaG by exp, colligative numbers recomputed from masses."""
import math, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk

C = Chk("materi/chemistry/physical-equilibrium.md")
ok = C.ok
R_LATM = 0.08206
R_J = 8.314

# ---- Example 1: for each option K, find the equilibrium of H2 + I2 <-> 2HI (1.00 M each) by bisection on x,
# and keep the K whose [HI] is 1.60 M. Then confirm with a rate-law simulation (kf = 1, kr = kf/K).
def hi_eq(K):
    lo, up = 0.0, 1.0
    for _ in range(200):
        x = (lo + up) / 2
        if (2 * x) ** 2 / ((1 - x) ** 2) > K:
            up = x
        else:
            lo = x
    return 2 * x


opts = C.options("**Example 1.**")
hits = [k for k, v in opts.items() if abs(hi_eq(float(v)) - 1.60) < 0.01]
ok(hits == ["D"], hits)
kr = 1.0 / 64
h2 = i2 = 1.00
prod = 0.0
dt = 1e-3
for _ in range(400_000):
    d = (1.0 * h2 * i2 - kr * prod * prod) * dt
    h2 -= d; i2 -= d; prod += 2 * d
ok(abs(prod - 1.60) < 0.005 and abs(h2 - 0.20) < 0.005, (prod, h2))
C.mcq2("**Example 1.**", 64, "D", tol=0.01)
C.opt2("**Example 1.**", "C", 1.6 / (0.2 * 0.2), tol=0.01)        # forgot to square HI
C.opt2("**Example 1.**", "A", 1 / 64, tol=0.03)                    # flipped
C.opt2("**Example 1.**", "B", 1.6 ** 2 / (0.8 * 0.8), tol=0.01)    # used 0.80 for H2
C.opt2("**Example 1.**", "E", 1.6 ** 2 / 0.2, tol=0.02)

# ---- Example 2: Kp = Kc (RT)^dn, with dn counted from the equation
dn = 2 - 1
kp = 0.0050 * (R_LATM * 400) ** dn
ok(abs(kp - 0.164) < 0.0005, kp)
# cross-check with pressures: pick concentrations obeying Kc, convert to partial pressures P = cRT, recompute K
c_n2o4 = 1.0
c_no2 = math.sqrt(0.0050 * c_n2o4)
p_n2o4, p_no2 = c_n2o4 * R_LATM * 400, c_no2 * R_LATM * 400
ok(abs(p_no2 ** 2 / p_n2o4 - kp) < 1e-9)
C.mcq2("**Example 2.**", 0.164, "C", tol=0.005)
C.opt2("**Example 2.**", "A", 0.0050 / (R_LATM * 400), tol=0.02)
C.opt2("**Example 2.**", "E", 1 / kp, tol=0.02)
C.opt2("**Example 2.**", "D", kp * 10, tol=0.005)

# ---- Q1: only T changes K; exothermic -> lower T raises K (van 't Hoff, dH = -198 kJ for the SO2 reaction)
dH = -198e3
K_at = lambda T: math.exp(-dH / R_J * (1 / T - 1 / 298.0))   # relative to K(298) = 1
ok(K_at(250) > K_at(298) > K_at(350))
ok(C.options("**1.**")["D"].startswith("decreasing the temperature") and C.key_letter(1) == "D")

# ---- Q2: K from dG
K2 = math.exp(5710 / (R_J * 298))
ok(abs(K2 - 10) < 0.05, K2)
C.mcq2("**2.**", 10, "C", tol=0.01)
C.opt2("**2.**", "B", math.log(K2), tol=0.01)
C.opt2("**2.**", "A", 1 / K2, tol=0.01)
# the 5.7 kJ per factor-10 shortcut
ok(abs(R_J * 298 * math.log(10) / 1000 - 5.705) < 0.01)

# ---- Q3: colligative numbers from masses
n = 20.0 / 58.4
m = n / 2.00
dT = 2 * 0.512 * m
ok(abs(dT - 0.175) < 0.0005, dT)
C.mcq2("**3.**", 0.175, "B", tol=0.005)
C.opt2("**3.**", "A", 0.512 * m, tol=0.005)               # forgot i
C.opt2("**3.**", "C", 2 * 0.512 * n / 1.00, tol=0.005)    # 1.00 kg
C.opt2("**3.**", "D", 0.512 * m / 2, tol=0.005)
C.opt2("**3.**", "E", n * 2, tol=0.005)                    # moles x 2, no Kb

# ---- Q4: dry ice: pressure 1 atm < triple-point pressure 5.11 atm -> no liquid at any temperature
P_trip, P_room = 5.11, 1.00
ok(P_room < P_trip)          # below the triple point pressure: only solid <-> gas boundary exists
ok(C.options("**4.**")["A"] == "It turns directly into a gas" and C.key_letter(4) == "A")

# ---- Q5: molar mass from density; compare with real molar masses of the candidate gases
M = 1.96 * R_LATM * 273.15 / 1.00
ok(abs(M - 44.0) < 0.3, M)
cands = {"A": 28.0, "B": 32.0, "C": 64.1, "D": 71.0, "E": 44.0}
best = min(cands, key=lambda k: abs(cands[k] - M))
ok(best == "E" and C.key_letter(5) == "E")
# every candidate has a distinct standard-state density; only CO2 gives 1.96
dens = {k: v / (R_LATM * 273.15) for k, v in cands.items()}
ok([k for k, d in dens.items() if abs(d - 1.96) < 0.01] == ["E"], dens)
C.letters_spread()
C.done()
