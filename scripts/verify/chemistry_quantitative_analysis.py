"""Independent checks for materi/chemistry/analytical-quantitative.md (examples + check questions).
Method: simulate the titration with a full charge-balance pH solver, not the shortcut formulas of the key."""
import math, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk

C = Chk("materi/chemistry/analytical-quantitative.md")
ok = C.ok
KW = 1e-14


def ph(vb_ml, ca, va_ml, cb, ka=None, acid_protons=1):
    """pH after adding vb_ml of strong base (cb M) to va_ml of acid (ca M). Full charge balance, bisection on [H+]."""
    vt = (va_ml + vb_ml) / 1000
    na = cb * vb_ml / 1000 / vt
    c_acid = ca * va_ml / 1000 / vt

    def f(h):
        anion = acid_protons * c_acid if ka is None else c_acid * ka / (ka + h)
        return h + na - KW / h - anion
    lo, hi = 1e-15, 10.0
    for _ in range(300):
        mid = math.sqrt(lo * hi)
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return -math.log10(mid)


def eq_volume(ca, va, cb, protons=1):
    """Volume of base where pH crosses 7 for a strong acid (scan in 0.01 mL steps)."""
    v = 0.0
    while ph(v, ca, va, cb, acid_protons=protons) < 7.0:
        v += 0.01
    return v


# Example 1: which concentration of H2SO4 (both H+ strong) has its pH-7 crossing at 30.00 mL?
opts = C.options("**Example 1.**")
hit = []
for k, t in opts.items():
    m = float(t.split()[0])
    if abs(eq_volume(m, 25.00, 0.100, protons=2) - 30.00) < 0.015:
        hit.append(k)
ok(hit == ["D"], hit)
C.mcq2("**Example 1.**", 0.0600, "D")
C.opt2("**Example 1.**", "C", 0.120)            # forgot factor 2
C.opt2("**Example 1.**", "B", 0.100 * 25 / 30, tol=0.002)  # flipped ratio
C.opt2("**Example 1.**", "E", 1.5 / 30)         # divided by titrant volume

# Example 2: Ka from pH 4.20 at 10.00 mL; test each option by simulating the titration
opts = C.options("**Example 2.**")
hit = []
for k, t in opts.items():
    ka, _ = __import__("chemistry_p2_helpers").parse(t)
    if abs(ph(10.00, 0.100, 20.00, 0.100, ka=ka) - 4.20) < 0.02:
        hit.append(k)
ok(hit == ["C"], hit)
ok(abs(10 ** -4.20 - 6.3e-5) < 0.03e-5)
C.mcq2("**Example 2.**", 6.3e-5, "C", tol=0.01)
C.opt2("**Example 2.**", "B", (10 ** -4.2) ** 2 / (1.00 / 30), tol=0.02)   # [H+]^2/[HA] with no A-
C.opt2("**Example 2.**", "D", 10 ** -4.8, tol=0.02)

# Q1 concept: weak acid + strong base, equivalence pH vs indicator ranges (Ka 1.8e-5, 0.100 M, 25 mL)
eq = ph(25.0, 0.100, 25.0, 0.100, ka=1.8e-5)
ok(8.2 < eq < 10.0 and not (6.0 < eq < 7.6) and not (3.1 < eq < 4.4), eq)
steep_lo, steep_hi = ph(24.9, 0.100, 25.0, 0.100, ka=1.8e-5), ph(25.1, 0.100, 25.0, 0.100, ka=1.8e-5)
ok(steep_lo < 8.2 + 2 and steep_hi > 10.0, (steep_lo, steep_hi))   # jump brackets phenolphthalein's window
C.text_key("**1.**", "C", "phenolphthalein")

# Q2 pool kit
n = 0.0200 * 7.50
c2 = n / 25.0
ok(abs(c2 - 0.00600) < 1e-12)
C.mcq2("**2.**", 0.00600, "A")
C.opt2("**2.**", "B", 0.0200 * 25.0 / 7.50, tol=0.002)
C.opt2("**2.**", "C", n / 32.5, tol=0.002)
C.opt2("**2.**", "D", n)

# Q3 quarter neutralized: pH from simulation (pKa 6): 25 mL 0.1 M HA + 6.25 mL 0.1 M NaOH
ka = 1e-6
p3 = ph(6.25, 0.100, 25.0, 0.100, ka=ka)
ok(abs(p3 - 5.52) < 0.01, p3)
C.mcq2("**3.**", 5.52, "E")
C.opt2("**3.**", "D", 6 + math.log10(3), tol=0.001)
C.opt2("**3.**", "B", 6 + math.log10(0.25), tol=0.003)
C.opt2("**3.**", "A", 5.00)

# Q4 Na2CO3 + HCl: brute force the stoichiometry step by step
mmol = 20.0 * 0.100
h_needed = 0.0
carbonate, bicarb, carbonic = mmol, 0.0, 0.0
step = 0.001
while carbonic < mmol - 1e-9:
    if carbonate > 1e-12:
        carbonate -= step; bicarb += step
    else:
        bicarb -= step; carbonic += step
    h_needed += step
v4 = h_needed / 0.100
ok(abs(v4 - 40.0) < 0.05, v4)
C.mcq2("**4.**", 40.0, "B")
C.opt2("**4.**", "A", 20.0)

# Q5 strong-strong excess OH
p5 = ph(30.0, 0.100, 25.0, 0.100)
ok(abs(p5 - 11.96) < 0.01, p5)
C.mcq2("**5.**", 11.96, "D")
C.opt2("**5.**", "A", -math.log10(0.5 / 55.0), tol=0.001)   # pOH
C.opt2("**5.**", "C", 14 + math.log10(0.5 / 25.0), tol=0.001)
C.opt2("**5.**", "E", 14 + math.log10(0.5 / 30.0), tol=0.001)
C.letters_spread()
C.done()
