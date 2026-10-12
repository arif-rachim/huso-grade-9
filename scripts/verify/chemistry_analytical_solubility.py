"""Independent checks for materi/chemistry/analytical-solubility.md."""
import sys, pathlib, math, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_inorganic_helpers import Checker

C = Checker("materi/chemistry/analytical-solubility.md")
ok = C.ok

def bisect(f, lo, hi, n=300):
    for _ in range(n):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0: hi = mid
        else: lo = mid
    return (lo + hi) / 2

def molar_solubility(ksp, m, n):
    """AmBn(s) <=> m A + n B ; [A] = m s, [B] = n s ; Ksp = (m s)^m (n s)^n. Solved by bisection."""
    return bisect(lambda s: (m * s) ** m * (n * s) ** n - ksp, 0.0, 1.0)

# ---- FACT_CHECKS: solubility rules used in the text and key
def soluble(cation, anion):
    if cation in ("Na+", "K+", "NH4+") or anion in ("NO3-", "CH3COO-"): return True
    if anion in ("Cl-", "Br-", "I-"): return cation not in ("Ag+", "Pb2+", "Hg2 2+")
    if anion == "SO4 2-": return cation not in ("Ba2+", "Pb2+", "Sr2+")
    if anion in ("CO3 2-", "PO4 3-", "S2-", "OH-", "O2-"): return False
    raise ValueError
ok(not soluble("Ca2+", "CO3 2-") and soluble("Na+", "NO3-") and soluble("NH4+", "SO4 2-") and soluble("K+", "Cl-") and soluble("Na+", "PO4 3-"))
ok(not soluble("Ag+", "Cl-") and not soluble("Ba2+", "SO4 2-") and soluble("Ca2+", "Cl-"))

# KNO3 curve is increasing, NaCl nearly flat (data used in the picture)
kno3 = [13, 32, 64, 110, 169, 246]; nacl = [35.7, 35.9, 36.4, 37.1, 38.0, 39.2]
ok(all(b > a for a, b in zip(kno3, kno3[1:])) and max(nacl) - min(nacl) < 4)
# the cooling arrow in the picture: 120 g at 80 C is below the KNO3 curve (169), at 20 C above it (32)
ok(120 < 169 and 120 > 32)

# ---- Example 1: CaF2
ksp = 3.2e-11
s = molar_solubility(ksp, 1, 2)
ok(abs(s - 2.0e-4) < 1e-7, s)
ok(abs(4 * s ** 3 - ksp) < 1e-20)
C.numopt("**Example 1.**", s, "B", tol=0.01)
C.distract("**Example 1.**", "A", math.sqrt(ksp), tol=0.01)
C.distract("**Example 1.**", "E", ksp ** (1 / 3), tol=0.01)
C.distract("**Example 1.**", "D", ksp / 4, tol=0.01)
C.distract("**Example 1.**", "C", ksp / 2, tol=0.01)
# AgCl: Ksp = s^2 ; Ca3(PO4)2 exponent pattern
ok(abs(molar_solubility(1.8e-10, 1, 1) - math.sqrt(1.8e-10)) < 1e-12)

# ---- Example 2: mixing
v1 = v2 = 0.100
ca = 2.0e-4 * v1 / (v1 + v2); co3 = 2.0e-4 * v2 / (v1 + v2)
ok(abs(ca - 1.0e-4) < 1e-16 and abs(co3 - 1.0e-4) < 1e-16)
Q = ca * co3
ksp_caco3 = 3.3e-9
ok(abs(Q - 1.0e-8) < 1e-20 and Q > ksp_caco3)
o = C.options("**Example 2.**")
def parse_opt(v):
    q = C.val(v.split(";")[0])
    return q, ("no precipitate" not in v and "precipitate forms" in v)
parsed = {k: parse_opt(v) for k, v in o.items()}
good = [k for k, (q, pp) in parsed.items() if abs(q - Q) < 1e-12 and pp == (Q > ksp_caco3)]
ok(good == ["B"], parsed)
ok(abs(parsed["A"][0] - 2.0e-4 * 2.0e-4) < 1e-12)          # no dilution
ok(abs(parsed["D"][0] - (ca + co3 + 0.0)) < 1e-12)          # added instead of multiplied
ok(abs(parsed["E"][0] - ksp_caco3) < 1e-12)
ok(C.key_letter(2) is not None and C.options("**Example 2.**")["B"].startswith("Q = 1.0 × 10⁻⁸"))

# ---- Q1 insoluble
opts = {"A": ("Na+", "NO3-"), "B": ("NH4+", "SO4 2-"), "C": ("Ca2+", "CO3 2-"), "D": ("K+", "Cl-"), "E": ("Na+", "PO4 3-")}
ok([k for k, (c, a) in opts.items() if not soluble(c, a)] == ["C"])
C.textopt("**1.**", "C", "CaCO₃")
# ---- Q2 supersaturated: concentration vs solubility at the cooler temperature (simple model)
def classify(amount, solub):
    return "unsaturated" if amount < solub else ("saturated" if amount == solub else "supersaturated")
ok(classify(200, 100) == "supersaturated" and classify(50, 100) == "unsaturated")
C.textopt("**2.**", "E", "supersaturated")
# ---- Q3 Ksp expression generated from the stoichiometry Ca3(PO4)2 -> 3 Ca + 2 PO4
def sup(n): return {1: "", 2: "²", 3: "³"}[n]
expr = f"[Ca²⁺]{sup(3)}[PO₄³⁻]{sup(2)}"
ok(C.options("**3.**")["A"] == expr, expr)
ok(C.options("**3.**")["B"] == "[Ca²⁺]²[PO₄³⁻]³")
C.ok(C.key_letter(3) == "A")
# ---- Q4 common-ion effect: s = Ksp/[Cl-] (valid because s << [Cl-]) ; bisection check too
ksp_agcl = 1.8e-10
def s_agcl(cl0):
    return bisect(lambda s: s * (cl0 + s) - ksp_agcl, 0.0, 1.0)
sol = {"A": s_agcl(0.0), "B": s_agcl(0.0) * 1.0, "C": None, "D": s_agcl(0.10), "E": s_agcl(0.010)}
ok(abs(sol["A"] - 1.34e-5) < 0.01e-5 and abs(sol["D"] - 1.8e-9) < 0.01e-9 and abs(sol["E"] - 1.8e-8) < 0.02e-8, sol)
ok(sol["D"] < sol["E"] < sol["A"])
C.textopt("**4.**", "D", "0.10 M NaCl")
# ---- Q5 gas solubility (Henry's law temperature dependence: reference data for CO2 in water, g/kg at 1 atm)
CO2 = {0: 3.35, 20: 1.69, 40: 0.97}
ok(CO2[0] > CO2[20] > CO2[40])
C.textopt("**5.**", "B", "less soluble in warm")
ok([C.key_letter(i) for i in range(1, 6)] == list("CEADB"))
C.done()
