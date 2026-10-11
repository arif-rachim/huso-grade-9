"""Independent checks for materi/chemistry/inorganic-isotopes.md."""
import sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_inorganic_helpers import Checker, Z

C = Checker("materi/chemistry/inorganic-isotopes.md")
ok = C.ok
ZSYM = {84: "Po", 82: "Pb", 86: "Rn", 85: "At", 87: "Fr", 88: "Ra", 89: "Ac", 90: "Th", 92: "U", 6: "C", 7: "N", 17: "Cl", 8: "O", 19: "K", 18: "Ar", 11: "Na", 12: "Mg"}
SYM2Z = {v: k for k, v in ZSYM.items()}
SUB = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉", "0123456789" + "0123456789")
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"; SUBS = "₀₁₂₃₄₅₆₇₈₉"

def parse(s):
    """'²²²₈₆Rn' -> (222, 86, 'Rn')"""
    m = re.match(rf"([{SUP}]+)([{SUBS}]+)([A-Za-z]+)", s.strip())
    a = int("".join(str(SUP.index(c)) for c in m.group(1)))
    z = int("".join(str(SUBS.index(c)) for c in m.group(2)))
    return a, z, m.group(3)

# decay rules: (dA, dZ)
DECAY = {"alpha": (-4, -2), "beta-": (0, +1), "beta+": (0, -1), "gamma": (0, 0), "neutron": (-1, 0)}
def decay(nuc, kind):
    a, z = nuc
    return a + DECAY[kind][0], z + DECAY[kind][1]

# ---- core ideas
ok(decay((238, 92), "alpha") == (234, 90) and ZSYM[90] == "Th")
ok(decay((14, 6), "beta-") == (14, 7) and ZSYM[7] == "N")
ok(238 == 234 + 4 and 92 == 90 + 2 and 14 == 14 + 0 and 6 == 7 - 1)
cl = 0.758 * 35 + 0.242 * 37
ok(abs(cl - 35.5) < 0.05 and abs(0.758 + 0.242 - 1) < 1e-12, cl)
ok(37 - 17 == 20 and 17 + 1 == 18)           # Cl-: neutrons, electrons
ok(11 - 1 == 10)                             # Na+ electrons
# half-life: fraction after n half-lives, brute force halving
frac = 1.0
for _ in range(2): frac /= 2
ok(frac == 0.25)

# ---- Example 1: weighted average
ar = 0.690 * 63 + 0.310 * 65
ok(abs(ar - 63.62) < 1e-9 and round(ar, 1) == 63.6, ar)
C.numopt("**Example 1.**", ar, "B", tol=0.002)
C.distract("**Example 1.**", "C", (63 + 65) / 2, tol=0)
C.distract("**Example 1.**", "D", 0.310 * 63 + 0.690 * 65, tol=0.001)
ok(abs(0.310 * 63 + 0.690 * 65 - 64.38) < 1e-9)
ok(abs(0.690 * 63 - 43.47) < 1e-9 and abs(0.310 * 65 - 20.15) < 1e-9)
ok(ar < (63 + 65) / 2)

# ---- Example 2: Ra-226 alpha then beta-
n = (226, 88)
n1 = decay(n, "alpha"); n2 = decay(n1, "beta-")
ok(n1 == (222, 86) and n2 == (222, 87), (n1, n2))
o = C.options("**Example 2.**")
parsed = {k: parse(v) for k, v in o.items()}
ok([k for k, (a, z, sym) in parsed.items() if (a, z) == n2] == ["B"])
for k, (a, z, sym) in parsed.items():
    ok(ZSYM[z] == sym, (k, sym))              # every option is a real (A, Z, symbol) combination
ok(parsed["A"][:2] == n1)                    # stops after alpha
ok(parsed["C"][:2] == decay(n1, "beta+"))     # wrong beta direction
ok(parsed["D"][:2] == (226, 87))             # forgot alpha lowers A
ok(parsed["E"][:2] == decay(n, "beta-"))      # only beta on radium
ok(C.key_letter(2) == "B")
ok(C.options("**Example 2.**")["B"] == "²²²₈₇Fr")

# ---- Q1 neutrons in 37Cl-
neutrons = 37 - 17
C.numopt("**1.**", neutrons, "E", tol=0)
C.distract("**1.**", "A", 17, tol=0); C.distract("**1.**", "B", 18, tol=0)
# ---- Q2 isotope pair: same Z, different A, neutral species
pairs = {"A": ("¹⁴₆C", "¹⁴₇N"), "B": ("¹²₆C", "¹⁴₆C"), "C": ("¹⁶₈O", "¹⁶₈O"), "D": ("³⁹₁₉K", "⁴⁰₁₈Ar"), "E": ("²³₁₁Na", "²⁴₁₂Mg")}
iso = []
for k, (x, y) in pairs.items():
    ax, zx, _ = parse(x + "X"); ay, zy, _ = parse(y + "X")
    if zx == zy and ax != ay: iso.append(k)
ok(iso == ["B"], iso)
ok(C.options("**2.**")["B"] == "¹²₆C and ¹⁴₆C")
ok(C.key_letter(2) == "B")
# ---- Q3 Po-210 alpha
a, z = decay((210, 84), "alpha")
ok((a, z) == (206, 82) and ZSYM[z] == "Pb")
o = C.options("**3.**")
vals = {k: tuple(int(x) for x in re.findall(r"\d+", v)) for k, v in o.items()}
ok([k for k, v in vals.items() if v == (206, 82)] == ["D"], vals)
ok(vals["B"] == (210 + 4, 84 + 2) and vals["A"] == (210, 82) and vals["C"] == (206, 86) and vals["E"] == decay((210, 84), "beta-"))
ok(C.key_letter(3) == "D")
# ---- Q4 half-lives by simulation
m = 80.0
t = 0.0
while t < 9.0 - 1e-9:
    m /= 2; t += 3.0
ok(m == 10.0)
C.numopt("**4.**", m, "A", tol=0)
ok(round(80 / 3, 1) == 26.7)
# ---- Q5 which decay: dA = 0, dZ = +1
hit = [k for k, d in zip("ABCDE", ["alpha", "gamma", "beta-", "beta+", "neutron"]) if DECAY[d] == (0, 1)]
ok(hit == ["C"])
C.textopt("**5.**", "C", "Beta-minus")
ok([C.key_letter(i) for i in range(1, 6)] == list("EBDAC"))
C.done()
