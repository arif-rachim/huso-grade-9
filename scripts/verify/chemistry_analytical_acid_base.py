"""Independent checks for materi/chemistry/analytical-acid-base.md."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_inorganic_helpers import Checker

C = Checker("materi/chemistry/analytical-acid-base.md")
ok = C.ok
KW = 1.0e-14

def bisect(f, lo, hi, n=200):
    """Root of a decreasing/increasing function by bisection (independent of the quadratic formulas in the text)."""
    for _ in range(n):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0: hi = mid
        else: lo = mid
    return (lo + hi) / 2

def ph_weak_acid(c, ka):
    # solve x^2/(c-x) = ka for x by bisection, ignoring water's own ionization
    x = bisect(lambda x: x * x / (c - x) - ka, 1e-14, c * (1 - 1e-12))
    return -math.log10(x), x

# ---- core ideas
ok(abs(KW / 1.0e-5 - 1.0e-9) < 1e-20)                  # Ka x Kb = Kw
ph, x = ph_weak_acid(0.10, 1.8e-5)
ok(abs(ph - 2.875) < 0.01, ph)
ok(x / 0.10 < 0.05, "less than 5 % ionized")
ok(abs(math.sqrt(1.8e-5 * 0.10) - 1.34e-3) < 0.005e-3)
# percent ionization grows on dilution (weak acid)
pcts = [ph_weak_acid(c, 1.8e-5)[1] / c for c in (0.1, 0.01, 0.001)]
ok(pcts[0] < pcts[1] < pcts[2])
# strong acid diluted 10x: pH rises by exactly 1 ; weak acid by about 0.5
ok(abs((-math.log10(0.001)) - (-math.log10(0.01)) - 1) < 1e-12)
dpH = ph_weak_acid(0.01, 1.8e-5)[0] - ph_weak_acid(0.1, 1.8e-5)[0]
ok(0.4 < dpH < 0.6, dpH)
ok(abs(-math.log10(0.001) - 3) < 1e-12)                  # 0.001 M HCl pH 3
ok(abs(10 ** 3 / 10 ** 4 - 0.1) < 1e-12)                  # pH 3 has 10x more H+ than pH 4
ok(abs(2 * 0.0050 - 0.010) < 1e-15)

# ---- Example 1
C.numopt("**Example 1.**", ph, "B", tol=0.02)
C.distract("**Example 1.**", "A", -math.log10(0.10), tol=0)
C.distract("**Example 1.**", "C", -math.log10(1.8e-5), tol=0.011)
C.distract("**Example 1.**", "D", -math.log10(1.8e-5 * 0.10), tol=0.011)
C.distract("**Example 1.**", "E", 14 - ph, tol=0.01)

# ---- Example 2: buffer by explicit mole bookkeeping
pka = 4.74
ha, a = 0.30, 0.60
ph0 = pka + math.log10(a / ha)
ok(abs(ph0 - 5.04) < 0.005)
ha2, a2 = ha + 0.10, a - 0.10               # HCl converts acetate into acetic acid
ph1 = pka + math.log10(a2 / ha2)
ok(abs(ph1 - 4.84) < 0.005 and abs(ha2 - 0.40) < 1e-12 and abs(a2 - 0.50) < 1e-12, ph1)
ok(abs(math.log10(1.25) - 0.097) < 0.001 and abs(ph0 - ph1 - 0.2) < 0.01)
C.numopt("**Example 2.**", ph1, "C", tol=0.002)
C.distract("**Example 2.**", "A", pka + math.log10(ha2 / a2), tol=0.002)   # inverted ratio
C.distract("**Example 2.**", "D", ph0, tol=0.002)
C.distract("**Example 2.**", "E", -math.log10(0.10), tol=0)
C.distract("**Example 2.**", "B", pka, tol=0)

# ---- Q1 conjugate acid of NH3 (add one H+ : formula bookkeeping)
def add_h(formula):
    return {"NH3": "NH4+", "H2O": "H3O+"}[formula]
ok(add_h("NH3") == "NH4+")
C.textopt("**1.**", "B", "NH₄⁺")
ok(C.options("**1.**")["D"] == "NH₂⁻")     # NH2- is NH3 minus H+
# ---- Q2 Ba(OH)2
oh = 2 * 0.0050
ph2 = 14 + math.log10(oh)
ok(abs(ph2 - 12.0) < 1e-9)
C.numopt("**2.**", ph2, "D", tol=1e-6)
C.distract("**2.**", "A", 14 + math.log10(0.0050), tol=0.005)
C.distract("**2.**", "B", -math.log10(oh), tol=0)
C.distract("**2.**", "C", -math.log10(0.0050), tol=0.01)
# ---- Q3 ratio of H+
ratio = 10 ** (7.4 - 6.4)
ok(abs(ratio - 10) < 1e-9)
C.numopt("**3.**", ratio, "A", tol=1e-6)
C.distract("**3.**", "B", 7.4 / 6.4, tol=0.005)
# ---- Q4 Lewis acid not Bronsted acid
cands = {"A": ("HCl", False, True), "B": ("H2O", False, True), "C": ("NH3", False, False), "D": ("OH-", False, False), "E": ("BF3", True, False)}
# (name, has empty orbital -> Lewis acid, can donate H+ -> Bronsted acid)
hits = [k for k, (n, lewis, bronsted) in cands.items() if lewis and not bronsted]
ok(hits == ["E"])
C.textopt("**4.**", "E", "BF₃")
# ---- Q5 lowest pH = largest Ka
kas = {"A": 1.8e-5, "B": 6.2e-10, "C": 6.8e-4, "D": 3.5e-8, "E": 4.0e-6}
o = C.options("**5.**")
ok({k: C.val(v) for k, v in o.items()} == kas)
phs = {k: ph_weak_acid(0.10, v)[0] for k, v in kas.items()}
ok(min(phs, key=phs.get) == "C" and abs(phs["C"] - 2.10) < 0.02 and abs(phs["A"] - 2.875) < 0.01, phs)
ok([C.key_letter(i) for i in range(1, 6)] == list("BDAEC"))
C.done()
