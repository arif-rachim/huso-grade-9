"""Independent checks for materi/physics/thermodynamics-ideal-gas.md (examples + check questions)."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/physics/thermodynamics-ideal-gas.md")
ok = C.ok
R = 8.315
ATM = 1.0e5

def integrate(p_of_v, v0, v1, n=200000):
    """Midpoint rule: work = area under P(V) (P in Pa, V in m^3)."""
    h = (v1 - v0) / n
    return sum(p_of_v(v0 + (k + 0.5) * h) for k in range(n)) * h

# Example 1: find n from the deep state with PV = nRT, then the volume at the surface (same T = 290 K, any T works)
T = 290.0
P_deep, V_deep = 3 * ATM, 2.0e-6
n_mol = P_deep * V_deep / (R * T)
V_surface = n_mol * R * T / (1 * ATM)
ok(abs(V_surface - 6.0e-6) < 1e-12, V_surface)
C.mcq("**Example 1.**", 6.0, "cm³", "D")
C.opt_is("**Example 1.**", "A", 2.0 * 1 / 3, "cm³", tol=0.01)       # ratio upside down: 2 x 1 / 3
C.opt_is("**Example 1.**", "C", 2.0 * 2 / 1, "cm³")                # 2 atm used at 20 m
C.opt_is("**Example 1.**", "E", 2.0 + 3, "cm³")                    # added
ok(3 * 2.0 == 1 * 6.0 and 2 * 3.0 == 6.0)                           # picture: P x V = 6
ok(1 + 20 / 10 == 3 and 1 + 10 / 10 == 2)                            # 1 atm per 10 m

# Example 2: rigid pot, find n from state 1, then P2 = nRT2/V (V fixed)
V = 0.005
P1 = 1.0 * ATM; T1 = 20 + 273; T2 = 120 + 273
n_mol = P1 * V / (R * T1)
P2 = n_mol * R * T2 / V / ATM
ok(abs(P2 - 1.341) < 0.001, P2)
C.mcq("**Example 2.**", P2, "atm", "B", tol=0.04)
C.opt_is("**Example 2.**", "D", 120 / 20, "atm")                    # Celsius ratio
C.opt_is("**Example 2.**", "A", T1 / T2, "atm", tol=0.01)           # flipped ratio 0.745 -> 0.75
ok(abs(T1 / T2 - 0.745) < 0.001)

# Q1: moles
n1 = 1.0e5 * 2.0e-3 / (R * (27 + 273))
C.mcq("**1.**", n1, "mol", "B", tol=0.01)
C.opt_is("**1.**", "C", 1.0e5 * 2.0e-3 / (R * 27), "mol", tol=0.01)   # Celsius
C.opt_is("**1.**", "D", 1.0e5 * 2.0 / (R * 300), "mol", tol=0.01)     # liters not converted
ok(abs(1.0e5 * 2.0e-3 - 200) < 1e-9 and abs(R * 300 - 2494.5) < 1e-9)

# Q2: constant pressure work, numerically
W2 = integrate(lambda v: 1.5e5, 2.0e-3, 5.0e-3, 1000)
C.mcq("**2.**", W2, "J", "E")
C.opt_is("**2.**", "A", 1.5e5 * 2.0e-3, "J")
C.opt_is("**2.**", "B", 1.5e5 * 5.0e-3, "J")
C.opt_is("**2.**", "C", 1.5e5 * 7.0e-3, "J")
C.opt_is("**2.**", "D", 1.5e5 * 3.0, "J")

# Q3: linear P(V), numerical area
def p3(v): return 3.0e5 + (1.0e5 - 3.0e5) * (v - 2.0e-3) / (6.0e-3 - 2.0e-3)
W3 = integrate(p3, 2.0e-3, 6.0e-3)
C.mcq("**3.**", W3, "J", "A", tol=0.001)
C.opt_is("**3.**", "B", 3.0e5 * 4.0e-3, "J")
C.opt_is("**3.**", "C", 1.0e5 * 4.0e-3, "J")
C.opt_is("**3.**", "D", (3.0e5 + 1.0e5) * 4.0e-3, "J")
C.opt_is("**3.**", "E", W3 * 1000, "J")

# Q4: Charles; find n from state 1 at fixed P, then V2
P = 1.0e5; V1 = 600e-6
n4 = P * V1 / (R * 300)
V2 = n4 * R * 450 / P * 1e6
ok(abs(V2 - 900) < 1e-6, V2)
C.mcq("**4.**", V2, "cm³", "C")
C.opt_is("**4.**", "A", 600 * 300 / 450, "cm³")
C.opt_is("**4.**", "B", 600 + (177 - 27), "cm³")
C.opt_is("**4.**", "D", 600 * 450 / 27, "cm³", tol=0.01)
C.opt_is("**4.**", "E", 600 * 177 / 27, "cm³", tol=0.01)
ok(177 + 273 == 450 and 27 + 273 == 300)

# Q5: isothermal work by numerical integration of nRT/V
n5, T5 = 1.0, 300.0
V0 = 1.0e-3
W5 = integrate(lambda v: n5 * R * T5 / v, V0, 2 * V0)
ok(abs(W5 - n5 * R * T5 * math.log(2)) < 0.01, W5)
ok(abs(W5 - 1729.06) < 0.05)
C.mcq("**5.**", W5, "J", "D", tol=0.002)
C.opt_is("**5.**", "A", -W5, "J", tol=0.002)
C.opt_is("**5.**", "B", n5 * R * 27 * 0.693, "J", tol=0.01)
C.opt_is("**5.**", "C", n5 * R * T5, "J", tol=0.002)
C.opt_is("**5.**", "E", n5 * R * T5 * 2, "J", tol=0.002)
# the picture numbers (idealgas-work.svg)
ok(abs(integrate(lambda v: 2e5, 1e-3, 3e-3, 10) - 400) < 1e-9)
ok(abs(integrate(lambda v: 4e5 - (v - 1e-3) * 1e8, 1e-3, 3e-3) - 600) < 0.01)
ok(abs(integrate(lambda v: 4e5 * 1e-3 / v, 1e-3, 2e-3) - 277.26) < 0.05)
# 1 mol = N_A particles: 0.5 mol has 3.0e23
ok(abs(0.5 * 6.022e23 - 3.011e23) < 1e17)
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
C.done()
