"""Independent checks for materi/chemistry/physical-thermo.md.
Method: Hess's law solved by brute force over integer combinations of the given equations; bond enthalpies counted from explicit
bond lists; lattice energy ranked with a Coulomb model; the heating-curve numbers recomputed from c and the molar enthalpies."""
import itertools, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk

C = Chk("materi/chemistry/physical-thermo.md")
ok = C.ok

# ---- Hess by brute force: a reaction is a dict species -> net coefficient (products +, reactants -)
SPECIES = ["C", "O2", "H2", "CH4", "CO2", "H2O", "CO"]


def vec(d):
    return tuple(d.get(s, 0) for s in SPECIES)


def combine(eqs, coeffs):
    tot = [0] * len(SPECIES)
    dh = 0.0
    for (v, h), c in zip(eqs, coeffs):
        tot = [a + c * b for a, b in zip(tot, v)]
        dh += c * h
    return tuple(tot), dh


# Example 1 from formation reactions: C + 2H2 -> CH4 ; C + O2 -> CO2 ; H2 + 1/2 O2 -> H2O(l)  (use doubled coefficients to stay integer)
FORM = [(vec({"C": -2, "H2": -4, "CH4": 2}), 2 * -74.8),
        (vec({"C": -1, "O2": -1, "CO2": 1}), -393.5),
        (vec({"H2": -2, "O2": -1, "H2O": 2}), 2 * -285.8)]
# target (doubled): 2CH4 + 4O2 -> 2CO2 + 4H2O
target = vec({"CH4": -2, "O2": -4, "CO2": 2, "H2O": 4})
found = []
for co in itertools.product(range(-6, 7), repeat=3):
    v, h = combine(FORM, co)
    if v == target:
        found.append(h / 2)
ok(len(found) == 1 and abs(found[0] + 890.3) < 1e-6, found)
C.mcq2("**Example 1.**", -890.3, "C", tol=0.0005)
C.opt2("**Example 1.**", "A", 890.3, tol=0.0005)
C.opt2("**Example 1.**", "B", -393.5 - 285.8 + 74.8, tol=0.0005)         # forgot the 2
C.opt2("**Example 1.**", "D", -393.5 + 2 * -285.8 + (-74.8), tol=0.0005)  # added reactants
C.opt2("**Example 1.**", "E", -393.5 + 2 * -241.8 + 74.8, tol=0.0005)     # H2O(g)

# Example 2: C + 1/2 O2 -> CO from (1) C + O2 -> CO2 and (2) CO + 1/2 O2 -> CO2 (doubled coefficients)
EQ = [(vec({"C": -2, "O2": -2, "CO2": 2}), 2 * -393.5), (vec({"CO": -2, "O2": -1, "CO2": 2}), 2 * -283.0)]
target2 = vec({"C": -2, "O2": -1, "CO": 2})
found = []
for co in itertools.product(range(-6, 7), repeat=2):
    v, h = combine(EQ, co)
    if v == target2:
        found.append(h / 2)
ok(found == [-110.5], found)
C.mcq2("**Example 2.**", -110.5, "B", tol=0.0005)
C.opt2("**Example 2.**", "A", -393.5 - 283.0, tol=0.0005)
C.opt2("**Example 2.**", "C", 110.5, tol=0.0005)
C.opt2("**Example 2.**", "E", 393.5 + 283.0, tol=0.0005)
ok(abs(-393.5) > abs(-110.5))   # sense check in step 5

# ---- Q1: boiling 500 g at 100 C
M = 18.0
n = 500 / M
ok(abs(n * 40.7 - 1130) < 1, n * 40.7)
C.mcq2("**1.**", n * 40.7, "B", tol=0.005)
C.opt2("**1.**", "A", n * 6.01, tol=0.005)
C.opt2("**1.**", "C", 500 * 40.7, tol=0.005)
C.opt2("**1.**", "D", 500 * 4.184 * 100 / 1000, tol=0.005)
C.opt2("**1.**", "E", 40.7, tol=0.001)

# ---- Q2: bond enthalpy sum from explicit bond lists
E = {"N#N": 945, "H-H": 436, "N-H": 391}
broken = {"N#N": 1, "H-H": 3}
formed = {"N-H": 2 * 3}           # 2 NH3, each N with 3 N-H bonds
dH = sum(E[b] * k for b, k in broken.items()) - sum(E[b] * k for b, k in formed.items())
ok(dH == -93, dH)
C.mcq2("**2.**", -93, "E", tol=0.001)
C.opt2("**2.**", "A", 93)
C.opt2("**2.**", "B", 945 + 3 * 436 - 3 * 391)
C.opt2("**2.**", "C", 945 + 436 - 6 * 391)
C.opt2("**2.**", "D", 945 + 3 * 436 - 2 * 391)
# H2 + Cl2 -> 2HCl in the core ideas
ok(436 + 243 - 2 * 431 == -183)

# ---- Q3: scan T for the sign change of dG = dH - T dS
dH3, dS3 = 6010.0, 22.0
t_switch = next(T for T in [x * 0.1 for x in range(1, 20000)] if dH3 - T * dS3 < 0)
ok(abs(t_switch - 273) < 0.5, t_switch)
C.mcq2("**3.**", 273, "C", tol=0.005)
C.opt2("**3.**", "A", 6.01 / 22.0, tol=0.005)
C.opt2("**3.**", "B", 22.0 / 6.01, tol=0.005)
C.opt2("**3.**", "E", 22.0 / 6.01 * 1000, tol=0.005)
# water's standard entropy of fusion is about dH/T at 273.15 K
ok(abs(6010 / 273.15 - 22.0) < 0.05)

# ---- Q4: Coulomb model  E ~ |q1 q2| / (r+ + r-)  (Shannon radii in pm)
ions = {"MgO": (2, 2, 72, 140), "NaCl": (1, 1, 102, 181), "KBr": (1, 1, 138, 196), "CsI": (1, 1, 167, 220), "LiF": (1, 1, 76, 133)}
score = {k: q1 * q2 / (rc + ra) for k, (q1, q2, rc, ra) in ions.items()}
rank = sorted(score, key=score.get, reverse=True)
ok(rank == ["MgO", "LiF", "NaCl", "KBr", "CsI"], rank)       # matches the real order 3791 > 1037 > 787 > 682 > 604 kJ/mol
opts = C.options("**4.**")
ok({k: v for k, v in opts.items()} == {"A": "MgO", "B": "NaCl", "C": "KBr", "D": "CsI", "E": "LiF"})
ok(C.key_letter(4) == "A")

# ---- Q5 first law, chemistry sign convention, and the physics form
q, w = -50, +200
dU = q + w
ok(dU == 150 and dU == q - (-w))          # physics: dU = Q - W with W by the gas = -200
C.mcq2("**5.**", 150, "D", tol=0.0)
C.opt2("**5.**", "C", q - w)
C.opt2("**5.**", "B", -q + w)
C.opt2("**5.**", "E", w)
C.opt2("**5.**", "A", -150)

# ---- numbers in the heating-curve picture
ok(abs(4.184 * 18.015 * 100 / 1000 - 7.54) < 0.01)
ok(abs(2.09 * 18.015 * 20 / 1000 - 0.75) < 0.01 and abs(1.84 * 18.015 * 20 / 1000 - 0.66) < 0.01)
ok(abs((-393.5 + 2 * -285.8) - (-965.1)) < 1e-9 and abs(-965.1 + 74.8 + 890.3) < 1e-9)
ok(abs(6.01 + 40.7 - 46.71) < 1e-9)
C.letters_spread()
C.done()
