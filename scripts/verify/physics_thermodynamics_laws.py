"""Independent checks for materi/physics/thermodynamics-laws.md (examples + check questions)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/physics/thermodynamics-laws.md")
ok = C.ok

def delta_U(heat_into_gas, work_done_on_gas):
    """Energy bookkeeping from the gas's point of view (independent of the 'Q - W' form)."""
    return heat_into_gas + work_done_on_gas

# Example 1: surroundings do 600 J ON the gas; gas loses 200 J of heat
dU = delta_U(-200, +600)
ok(dU == 400)
C.mcq("**Example 1.**", dU, "J", "C")
ok(-200 - (-600) == dU, "Q - W with W = -600")
C.opt_is("**Example 1.**", "A", -200 - (+600), "J")      # W = +600 (work BY gas)
C.opt_is("**Example 1.**", "D", +200 - (-600), "J")      # Q = +200
C.opt_is("**Example 1.**", "E", 600, "J")                # forgot the heat
C.opt_is("**Example 1.**", "B", +200 - (+600), "J")      # extra: both signs flipped

# Example 2: Carnot limit via kelvin; brute force check that no efficiency above it is allowed by the entropy balance
Th, Tc, Qh = 227 + 273, 27 + 273, 1000.0
ok((Th, Tc) == (500, 300))
def entropy_ok(W):
    """Second law bookkeeping: dumped heat Qc = Qh - W must satisfy Qc/Tc >= Qh/Th (total entropy does not drop)."""
    Qc = Qh - W
    return Qc / Tc >= Qh / Th - 1e-12
best = max(w for w in range(0, 1001) if entropy_ok(w))
ok(best == 400, best)
C.mcq("**Example 2.**", best, "J", "B")
ok(abs((1 - Tc / Th) * Qh - 400) < 1e-9)
C.opt_is("**Example 2.**", "D", (1 - 27 / 227) * Qh, "J", tol=0.002)   # Celsius numbers
C.opt_is("**Example 2.**", "A", 27 / 227 * Qh, "J", tol=0.005)         # 27/227 as the efficiency
C.opt_is("**Example 2.**", "C", Tc / Th * Qh, "J")                      # wasted share
C.opt_is("**Example 2.**", "E", Qh, "J")
ok(not entropy_ok(1000) and not entropy_ok(401) and entropy_ok(400), "100% engine forbidden")
ok(Qh - 400 == 600, "600 J dumped")
# picture numbers: 1000 = 400 + 600, e = 40%, and 1 - 300/500 = 40%
ok(400 + 600 == 1000 and abs(400 / 1000 - (1 - 300 / 500)) < 1e-12)

# Q1 concept: key is D and option D mentions the zeroth law, no other option does
o = C.options("**1.**")
ok(C.key_letter(1) == "D" and "zeroth" in o["D"] and all("zeroth" not in o[k] for k in "ABCE"))

# Q2: insulated expansion
dU2 = delta_U(0, -250)
ok(dU2 == -250)
C.mcq("**2.**", dU2, "J", "A")
C.opt_is("**2.**", "B", 250, "J")
C.opt_is("**2.**", "C", 0, "J")
ok(0 - 250 == dU2)

# Q3: concept; E is the only option that needs heat to flow cold -> hot
o3 = C.options("**3.**")
ok(C.key_letter(3) == "E" and "hotter while the air gets cooler" in o3["E"])
# energy bookkeeping: a hot coffee (T_c) and cool air (T_a): entropy change of "coffee heats up by q from air" is negative
q, Tcoffee, Tair = 100.0, 340.0, 295.0
ds_reverse = q / Tcoffee - q / Tair      # coffee gains q (hotter), air loses q
ds_normal = -q / Tcoffee + q / Tair      # coffee loses q to the air
ok(ds_reverse < 0 < ds_normal, "reverse flow lowers total entropy; normal flow raises it")
ok(abs((+q) + (-q)) == 0, "energy conserved either way")

# Q4: engine
Qc = 1200 - 300
C.mcq("**4.**", Qc, "J", "B")
C.opt_is("**4.**", "A", 300, "J")
C.opt_is("**4.**", "C", 1200, "J")
C.opt_is("**4.**", "D", 1200 + 300, "J")
C.opt_is("**4.**", "E", 1200 / (300 / 1200), "J")
ok(300 / 1200 == 0.25)

# Q5: absolute zero
o5 = C.options("**5.**")
ok(C.key_letter(5) == "C" and "273" in o5["C"] and abs((0 - 273.15) - (-273)) < 0.5)
ok(all("273" not in o5[k] for k in "ABDE"))
# Kelvin conversions used in the picture
ok(20 + 273 == 293 and 0 + 273 == 273)

letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
C.done()
