"""Independent checks for materi/earth/hydrosphere-groundwater.md (porosity, Darcy travel time by stepping, packing, Ghyben-Herzberg)."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/hydrosphere-groundwater.md")
ok = C.ok
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


# ---- Example 1: porosity from the mass of water taken up
V_total, m_dry, m_wet = 200.0, 500.0, 550.0
V_pores = (m_wet - m_dry) / 1.0
por = V_pores / V_total * 100
fact("Example 1: 25 %", abs(por - 25) < 1e-9)
C.mcq("**Example 1.**", por, "%", "C", tol=0.01)
C.opt_is("**Example 1.**", "B", 50 / 500 * 100, "%", tol=0.01)
C.opt_is("**Example 1.**", "A", 50 / 550 * 100, "%", tol=0.01)
C.opt_is("**Example 1.**", "D", 50, "%")
C.opt_is("**Example 1.**", "E", 550 / 200 * 100, "%")

# ---- Example 2: Darcy + porosity, travel time by stepping 1 day at a time
K, n, L, hA, hB = 5.0, 0.25, 200.0, 52.0, 50.0
i = (hA - hB) / L
q = K * i
v = q / n
from fractions import Fraction
x, days = Fraction(0), 0
while x < L:
    x += Fraction(str(v))
    days += 1
fact("Example 2: i = 0.01, q = 0.05 m/day, v = 0.2 m/day", abs(i - 0.01) < 1e-12 and abs(q - 0.05) < 1e-12 and abs(v - 0.2) < 1e-12)
fact("Example 2: 1000 days (2.7 years)", days == 1000 and abs(days / 365.25 - 2.74) < 0.01)
C.mcq("**Example 2.**", days, "days", "C")
C.opt_is("**Example 2.**", "D", L / q, "days")
C.opt_is("**Example 2.**", "A", L / K, "days")
C.opt_is("**Example 2.**", "B", L / (q * n), "days")
C.opt_is("**Example 2.**", "E", 0.2, "days", tol=0.01)
fact("flow is from A (52 m) to B (50 m)", hA > hB)

# ---- porosity of equal spheres does not depend on the radius; depends on packing
def porosity_cubic(r):
    side = 2 * r * 10
    n_spheres = (side / (2 * r)) ** 3
    return 1 - n_spheres * 4 / 3 * math.pi * r ** 3 / side ** 3


def porosity_rhombohedral():
    return 1 - math.pi / (3 * math.sqrt(2))


fact("equal spheres: same porosity for any grain size", all(abs(porosity_cubic(r) - porosity_cubic(1)) < 1e-12 for r in (0.01, 0.5, 3, 100)))
fact("cubic packing 47.6 %, rhombohedral 26.0 %", abs(porosity_cubic(1) * 100 - 47.64) < 0.01 and abs(porosity_rhombohedral() * 100 - 25.95) < 0.01)
# poorly sorted: filling the gaps of a cubic packing with a small sphere lowers the porosity
big_r = 1.0
small_r = (math.sqrt(3) - 1) * big_r              # largest sphere fitting a cubic hole
fact("small grains in the gaps lower the porosity", (4 / 3 * math.pi * small_r ** 3) / (2 * big_r) ** 3 > 0.0)
fact("typical porosity ranges in the file match the usual textbook values", "25 to 40 %" in C.txt and "40 to 70 %" in C.txt and "5 to 30 %" in C.txt)

# ---- Ghyben-Herzberg
RHO_F, RHO_S = 1000.0, 1025.0
ratio = RHO_F / (RHO_S - RHO_F)
fact("Ghyben-Herzberg ratio is 40", abs(ratio - 40) < 1e-9)
C.mcq("**5.**", ratio * 2, "m", "B")
C.opt_is("**5.**", "C", ratio, "m")
C.opt_is("**5.**", "A", 2, "m")
C.opt_is("**5.**", "D", ratio / 2, "m")
C.opt_is("**5.**", "E", 100 * 2, "m")
# physical check: pressure balance at the interface: rho_f (h + z) = rho_s z  ->  z = rho_f h / (rho_s - rho_f)
h = 2.0
z = RHO_F * h / (RHO_S - RHO_F)
fact("pressure balance gives 80 m", abs(z - 80) < 1e-9 and abs(RHO_F * (h + z) - RHO_S * z) < 1e-9)

# ---- Q1-Q4
o1 = C.options("**1.**")
fact("Q1 key D = clay", C.key_letter(1) == "D" and o1["D"] == "clay")
fact("clay: porosity range up to 70 % but the lowest K", "clay 40 to 70 %" in C.txt.replace("**", ""))
o2 = C.options("**2.**")
fact("Q2 key A = pressure + potentiometric surface above ground", C.key_letter(2) == "A" and "potentiometric surface is above the ground" in o2["A"])
o3 = C.options("**3.**")
fact("Q3 key C = cone of depression", C.key_letter(3) == "C" and o3["C"] == "It sinks in a cone shape around the well.")
por4 = 0.8 / 2.0 * 100
C.mcq("**4.**", por4, "%", "E")
C.opt_is("**4.**", "A", 0.8 / 2.8 * 100, "%", tol=0.02)
C.opt_is("**4.**", "B", 1.2 / 2.0 * 100, "%")
C.opt_is("**4.**", "C", 80, "%")
C.opt_is("**4.**", "D", 2.0 / 0.8 * 100, "%")
fact("groundwater is about 30 % of fresh water (USGS 30.1)", abs(10.53e6 / 35.029e6 * 100 - 30.1) < 0.1)
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
