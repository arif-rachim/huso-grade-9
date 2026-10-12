"""Independent checks for materi/chemistry/inorganic-reactions.md."""
import sys, pathlib, itertools, re
from collections import Counter
from fractions import Fraction
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_inorganic_helpers import Checker, M

C = Checker("materi/chemistry/inorganic-reactions.md")
ok = C.ok
NA, VM = 6.02e23, 22.4

def parse(formula):
    """'C2H6' or 'Ca(OH)2' -> Counter of atoms."""
    def rec(s):
        cnt = Counter(); i = 0
        while i < len(s):
            if s[i] == "(":
                j = s.index(")", i)
                m = re.match(r"\d*", s[j + 1:]); k = int(m.group()) if m.group() else 1
                for el, n in rec(s[i + 1:j]).items(): cnt[el] += n * k
                i = j + 1 + len(m.group())
            else:
                m = re.match(r"([A-Z][a-z]?)(\d*)", s[i:])
                cnt[m.group(1)] += int(m.group(2)) if m.group(2) else 1
                i += len(m.group(0))
        return cnt
    return rec(formula)

def molar(formula):
    return sum(M[el] * n for el, n in parse(formula).items())

def balanced(lhs, rhs):
    """lhs/rhs: list of (coef, formula)."""
    def tot(side):
        c = Counter()
        for k, f in side:
            for el, n in parse(f).items(): c[el] += k * n
        return c
    return tot(lhs) == tot(rhs)

# ---- core ideas
ok(molar("H2O") == 18 and molar("CO2") == 44 and molar("O2") == 32 and molar("H2") == 2)
ok(sum(parse("H2O").values()) == 3)
ok(balanced([(1, "C3H8"), (5, "O2")], [(3, "CO2"), (4, "H2O")]))
ok(molar("C6H12O6") == 180 and molar("CH2O") * 6 == 180)
ok(molar("H2O2") == 34)
ok(abs(Fraction(18, 1) / 1 - 18) == 0)
# sandwich: 2 bread + 1 cheese
bread, cheese = 10, 3
sand = min(bread // 2, cheese // 1)
ok(sand == 3 and bread - 2 * sand == 4)
# dilution conserves moles
ok(abs(0.5 * 0.2 - 0.1 * 1.0) < 1e-12)

# ---- Example 1: baking soda
ok(molar("NaHCO3") == 84)
n = 8.4 / molar("NaHCO3")
ok(abs(n - 0.10) < 1e-12)
ok(balanced([(1, "NaHCO3"), (1, "CH3COOH")], [(1, "CH3COONa"), (1, "H2O"), (1, "CO2")]))
v = n * 1 * VM
ok(abs(v - 2.24) < 1e-9)
C.numopt("**Example 1.**", v, "C")
C.distract("**Example 1.**", "A", 0.224); C.distract("**Example 1.**", "B", n * 0.5 * VM); C.distract("**Example 1.**", "D", n * 2 * VM)
C.distract("**Example 1.**", "E", 8.4)

# ---- Example 2: limiting reactant by brute force over extent of reaction
nH2, nO2 = 4.0 / molar("H2"), 40 / molar("O2")
ok(nH2 == 2.0 and nO2 == 1.25)
best = 0.0
for k in range(0, 4001):
    xi = k / 1000       # extent in mol (2 H2 + O2 -> 2 H2O)
    if 2 * xi <= nH2 + 1e-12 and xi <= nO2 + 1e-12:
        best = max(best, xi)
m_h2o = 2 * best * molar("H2O")
ok(abs(m_h2o - 36) < 1e-9, m_h2o)
C.numopt("**Example 2.**", m_h2o, "B")
ok(nH2 / 2 < nO2 / 1)                      # H2 is limiting
C.distract("**Example 2.**", "C", nO2 * 2 * 18)     # O2 limiting assumed
C.distract("**Example 2.**", "E", 4.0 + 40)         # sum of masses
C.distract("**Example 2.**", "D", 1.25 * 18)
C.distract("**Example 2.**", "A", 18)
ok(abs((4.0 + 40) - m_h2o - (nO2 - best) * molar("O2")) < 1e-9, "mass conservation: leftover O2")
ok(abs((nO2 - best) * 32 - 8) < 1e-9)

# ---- Q1 balancing by brute force
sol = None
for a, b, c, d in itertools.product(range(1, 10), repeat=4):
    if balanced([(a, "C2H6"), (b, "O2")], [(c, "CO2"), (d, "H2O")]):
        if sol is None or a + b + c + d < sum(sol): sol = (a, b, c, d)
ok(sol == (2, 7, 4, 6), sol)
C.numopt("**1.**", sol[1], "D", tol=0)
# ---- Q2 empirical formula
pct = {"C": 40.0, "H": 6.7, "O": 53.3}
mol = {el: p / M[el] for el, p in pct.items()}
small = min(mol.values())
ratio = {el: v / small for el, v in mol.items()}
ok(all(abs(r - round(r)) < 0.02 for r in ratio.values()) and [round(ratio[e]) for e in "CHO"] == [1, 2, 1], ratio)
o = C.options("**2.**")
ok(o["A"] == "CH₂O")
wholes = {"A": (1, 2, 1), "B": (2, 4, 1), "C": (1, 1, 1), "D": (2, 2, 1), "E": (1, 4, 2)}
ok([k for k, v in wholes.items() if v == (1, 2, 1)] == ["A"])
ok(C.key_letter(2) == "A")
ok(abs(sum(pct.values()) - 100) < 1e-9)
# ---- Q3 NaOH
nn = 0.20 * 0.250
mm = nn * 40
ok(abs(mm - 2.0) < 1e-12)
C.numopt("**3.**", mm, "E")
C.distract("**3.**", "A", 0.20 * 1 * 40); C.distract("**3.**", "B", nn); C.distract("**3.**", "C", 0.20 * 2.5 * 40); C.distract("**3.**", "D", 0.20 * 0.025 * 40)
# ---- Q4 atoms
samples = {"A": (16, "CH4"), "B": (36, "H2O"), "C": (22, "CO2"), "D": (32, "O2"), "E": (40, "Ar")}
M2 = dict(M); M2["Ar"] = 40
def atoms(g, f):
    base = parse(f) if f != "Ar" else Counter({"Ar": 1})
    mass = sum(M2[e] * c for e, c in base.items())
    return g / mass * sum(base.values())
res = {k: atoms(*v) for k, v in samples.items()}
ok(max(res, key=res.get) == "B" and res == {"A": 5.0, "B": 6.0, "C": 1.5, "D": 2.0, "E": 1.0}, res)
C.textopt("**4.**", "B", "36 g of H₂O")
# ---- Q5 types
eqs = {"A": ([(2, "Mg"), (1, "O2")], [(2, "MgO")], "synthesis"),
       "B": ([(1, "CaCO3")], [(1, "CaO"), (1, "CO2")], "decomposition"),
       "C": ([(1, "AgNO3"), (1, "NaCl")], [(1, "AgCl"), (1, "NaNO3")], "double"),
       "D": ([(1, "Zn"), (1, "CuSO4")], [(1, "ZnSO4"), (1, "Cu")], "single"),
       "E": ([(1, "CH4"), (2, "O2")], [(1, "CO2"), (2, "H2O")], "combustion")}
for k, (l, r, kind) in eqs.items():
    ok(balanced(l, r), k)
    n_l, n_r = len(l), len(r)
    # classify mechanically
    if n_l == 2 and n_r == 1: guess = "synthesis"
    elif n_l == 1 and n_r >= 2: guess = "decomposition"
    elif any(f == "O2" for _, f in l) and any(f == "CO2" for _, f in r): guess = "combustion"
    elif any(len(parse(f)) == 1 for _, f in l) and n_l == 2: guess = "single"
    else: guess = "double"
    ok(guess == kind, (k, guess))
C.textopt("**5.**", "C", "AgNO₃")
ok([C.key_letter(i) for i in range(1, 6)] == list("DAEBC"))
C.done()
