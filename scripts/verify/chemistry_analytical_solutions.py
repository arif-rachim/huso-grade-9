"""Independent checks for materi/chemistry/analytical-solutions.md."""
import sys, pathlib, math, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_inorganic_helpers import Checker, M

C = Checker("materi/chemistry/analytical-solutions.md")
ok = C.ok
KW = 1.0e-14

def solve_weak(c, k, base=False):
    """Exact pH of a weak acid (or base) of analytical concentration c: x^2/(c-x) = k, quadratic formula."""
    x = (-k + math.sqrt(k * k + 4 * k * c)) / 2
    return x

# ---- FACT_CHECKS: reference constants
KA = {"CH3COOH": 1.8e-5, "NH4+": 5.6e-10, "HCO3-": 4.7e-11, "Al(H2O)6 3+": 1.4e-5}
KW50 = 5.5e-14

# ---- core ideas
kb = KW / KA["CH3COOH"]
ok(abs(kb - 5.56e-10) < 0.01e-10, kb)
oh = math.sqrt(kb * 0.10)
ok(abs(oh - 7.45e-6) < 0.05e-6)
poh = -math.log10(oh)
ok(round(poh, 2) == 5.13 and round(14 - poh, 1) == 8.9, poh)
# conversion formula M = 10 * % * rho / M_solute for 37 % HCl, 1.18 g/mL
molar_hcl = 10 * 37 * 1.18 / 36.5
ok(abs(molar_hcl - 11.96) < 0.01)
# mass percent -> molarity by brute force: 1000 mL solution
mass = 1000 * 1.18; hcl = mass * 0.37; ok(abs(hcl / 36.5 - molar_hcl) < 1e-9)
# Kb = Kw / Ka by multiplication
ok(abs(KA["CH3COOH"] * kb - KW) < 1e-20)
# mole fraction and ppm definitions (spot checks)
ok(abs(2.0 / (2.0 + 55.5) - 0.0348) < 1e-3)

# ---- Example 1: molality and molarity
n = 117 / (23 + 35.5)
ok(abs(n - 2.0) < 1e-12)
molality = n / 2.0
molarity = n / 2.1
ok(molality == 1.0 and abs(molarity - 0.952) < 1e-3)
o = C.options("**Example 1.**")
def two(v):
    a, b = re.findall(r"\d+(?:\.\d+)?", v)
    return float(a), float(b)
vals = {k: two(v) for k, v in o.items()}
ok([k for k, (a, b) in vals.items() if abs(a - molality) < 1e-9 and abs(b - molarity) < 0.006] == ["A"], vals)
ok(vals["B"] == (0.95, 1.0) and vals["C"] == (1.0, 1.0) and abs(vals["D"][0] - n / 1.0) < 1e-9 and vals["E"] == (1.0, 2.0))
ok(abs(n / 1.0 - 2.0) < 1e-9)    # D: divided by 1 kg;  E: divided by 1 L gives molarity 2.0
ok(C.options("**Example 1.**")["A"] == "1.0 m and 0.95 M")

# ---- Example 2: Kw at 50 C
h = math.sqrt(KW50)
ph = -math.log10(h)
ok(abs(h - 2.345e-7) < 0.001e-7 and round(ph, 2) == 6.63, ph)
C.numopt("**Example 2.**", ph, "B", tol=0.001)
C.distract("**Example 2.**", "C", -math.log10(KW50), tol=0.001)      # pKw
C.distract("**Example 2.**", "E", -math.log10(math.sqrt(5.5e-13)), tol=0.001)
C.distract("**Example 2.**", "A", 7.0, tol=0); C.distract("**Example 2.**", "D", 14 - ph, tol=0.001)
ok(abs(h * h - KW50) < 1e-25)    # [H+] = [OH-] -> neutral

# ---- Q1 dilution
c2 = 2.0 * 50 / 200
C.numopt("**1.**", c2, "C", tol=0)
C.distract("**1.**", "D", 2.0 / 8, tol=0); C.distract("**1.**", "A", 2.0 * 4, tol=0)
# ---- Q2 molality
tempdep = {"A": True, "B": True, "C": True, "D": True, "E": False}      # volume-based units change with temperature
ok([k for k, v in tempdep.items() if not v] == ["E"])
C.textopt("**2.**", "E", "Molality")
# ---- Q3 [H+]
hplus = KW / 1.0e-3
ok(abs(hplus - 1.0e-11) < 1e-20)
C.numopt("**3.**", hplus, "A", tol=1e-6)
# ---- Q4/Q5: pH of salt solutions from constants
salts = {
    "NaCl": 7.0, "KNO3": 7.0, "KBr": 7.0,
    "CH3COONa": 14 + math.log10(solve_weak(0.1, KW / KA["CH3COOH"])),
    "Na2CO3": 14 + math.log10(solve_weak(0.1, KW / KA["HCO3-"])),
    "NH4Cl": -math.log10(solve_weak(0.1, KA["NH4+"])),
    "AlCl3": -math.log10(solve_weak(0.1, KA["Al(H2O)6 3+"])),
}
ok(abs(salts["CH3COONa"] - 8.87) < 0.01 and abs(salts["Na2CO3"] - 11.66) < 0.02 and abs(salts["NH4Cl"] - 5.13) < 0.01 and abs(salts["AlCl3"] - 2.93) < 0.02, salts)
o4 = {"A": "NaCl", "B": "KNO3", "C": "CH3COONa", "D": "NH4Cl", "E": "Na2CO3"}
ok([k for k, s in o4.items() if salts[s] < 7] == ["D"])
C.textopt("**4.**", "D", "NH₄Cl")
o5 = {"A": "NaCl", "B": "Na2CO3", "C": "NH4Cl", "D": "KBr", "E": "AlCl3"}
ok(max(o5, key=lambda k: salts[o5[k]]) == "B")
C.textopt("**5.**", "B", "Na₂CO₃")
ok([C.key_letter(i) for i in range(1, 6)] == list("CEADB"))
C.done()
