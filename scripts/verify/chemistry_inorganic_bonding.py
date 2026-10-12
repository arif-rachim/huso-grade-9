"""Independent checks for materi/chemistry/inorganic-bonding.md."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_inorganic_helpers import Checker

C = Checker("materi/chemistry/inorganic-bonding.md")
ok = C.ok

# ---- FACT_CHECKS (reference data)
BP = {"H2O": 100, "H2S": -60.3, "H2Se": -41.3, "H2Te": -2, "CH4": -161.5, "SiH4": -112, "GeH4": -88.5, "SnH4": -52,
      "HCl": -85, "Ne": -246.1}
EN = {"H": 2.20, "C": 2.55, "N": 3.04, "O": 3.44, "F": 3.98, "S": 2.58, "Cl": 3.16}
VAL = {"H": 1, "C": 4, "N": 5, "O": 6, "S": 6, "B": 3, "P": 5}
# the picture of boiling points
ok([BP[k] for k in ("H2O", "H2S", "H2Se", "H2Te")] == [100, -60.3, -41.3, -2])
ok(BP["H2S"] > BP["CH4"] and BP["H2O"] > BP["H2Te"], "water is far above the trend")
ok(BP["SiH4"] < BP["GeH4"] < BP["SnH4"])

# ---- VSEPR bookkeeping: steric number = (valence electrons of centre + monovalent ligands)/2 ; O/S ligands (=O) add 0
def steric(centre, ligands):
    mono = sum(1 for l in ligands if l in ("H", "F", "Cl"))
    sn = (VAL[centre] + mono) / 2
    assert sn == int(sn), (centre, ligands)
    return int(sn)
def shape(centre, ligands):
    sn, nb = steric(centre, ligands), len(ligands)
    lp = sn - nb
    table = {(2, 0): "linear", (3, 0): "trigonal planar", (3, 1): "bent", (4, 0): "tetrahedral",
             (4, 1): "trigonal pyramidal", (4, 2): "bent"}
    return table[(sn, lp)], sn, lp
ok(shape("C", ["O", "O"]) == ("linear", 2, 0))
ok(shape("B", ["F"] * 3) == ("trigonal planar", 3, 0))
ok(shape("S", ["O", "O"]) == ("bent", 3, 1))
ok(shape("C", ["H"] * 4) == ("tetrahedral", 4, 0))
ok(shape("N", ["H"] * 3) == ("trigonal pyramidal", 4, 1))
ok(shape("O", ["H"] * 2) == ("bent", 4, 2))
ok(shape("S", ["O"] * 3) == ("trigonal planar", 3, 0))
HYB = {2: "sp", 3: "sp2", 4: "sp3", 5: "sp3d", 6: "sp3d2"}
ok(HYB[steric("C", ["O", "O"])] == "sp" and HYB[steric("N", ["H"] * 3)] == "sp3")

# ---- Example 1: net dipoles from vectors (ideal geometry)
def unit(a_deg):
    return (math.cos(math.radians(a_deg)), math.sin(math.radians(a_deg)))
def net(centre, ligands, vecs):
    x = y = 0.0
    for lig, (vx, vy) in zip(ligands, vecs):
        d = EN[lig] - EN[centre]          # points toward the more electronegative atom
        x += d * vx; y += d * vy
    return math.hypot(x, y)
# tetrahedral unit vectors in 3D
tet = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
tet = [tuple(c / math.sqrt(3) for c in v) for v in tet]
def net3(centre, ligands, vecs):
    s = [0, 0, 0]
    for lig, v in zip(ligands, vecs):
        d = EN[lig] - EN[centre]
        for k in range(3): s[k] += d * v[k]
    return math.sqrt(sum(c * c for c in s))
h2o = net("O", ["H", "H"], [unit(-90 + 104.5 / 2), unit(-90 - 104.5 / 2)])
so2 = net("S", ["O", "O"], [unit(-90 + 119 / 2), unit(-90 - 119 / 2)])
ccl4 = net3("C", ["Cl"] * 4, tet)
chcl3 = net3("C", ["H", "Cl", "Cl", "Cl"], tet)
# NH3: three N-H bonds at 107 deg to each other: build pyramid by angle between bonds
def pyramid(theta):
    # find polar angle a so that angle between two bonds 120 deg apart in azimuth equals theta
    c = math.cos(math.radians(theta))
    # cos(theta) = sin^2(a) cos(120) + cos^2(a)  ->  cos^2 a (1 - cos120) = c - cos120 ... solve numerically
    for a in [i / 1000 for i in range(0, 1571)]:
        if abs(math.sin(a) ** 2 * math.cos(math.radians(120)) + math.cos(a) ** 2 - c) < 1e-3:
            return a
nh3a = pyramid(107)
vecs = [(math.sin(nh3a) * math.cos(math.radians(az)), math.sin(nh3a) * math.sin(math.radians(az)), -math.cos(nh3a)) for az in (0, 120, 240)]
nh3 = net3("N", ["H"] * 3, vecs)
ok(h2o > 0.3 and so2 > 0.3 and nh3 > 0.2 and chcl3 > 0.2, (h2o, so2, nh3, chcl3))
ok(ccl4 < 1e-9, ccl4)
nonpolar = [k for k, v in {"A": h2o, "B": nh3, "C": so2, "D": ccl4, "E": chcl3}.items() if v < 1e-6]
ok(nonpolar == ["D"])
C.textopt("**Example 1.**", "D", "CCl₄")
ok(C.options("**Example 1.**")["E"] == "CHCl₃")

# ---- Example 2: hybridization of acrylonitrile H2C=CH-C#N from the structure
atoms = {"C1": ["H", "H", "C2"], "C2": ["H", "C1", "C3"], "C3": ["C2", "N"]}       # sigma neighbours; pi bonds are not domains
hyb = [HYB[len(v)] for v in atoms.values()]      # no lone pairs on carbon
ok(hyb == ["sp2", "sp2", "sp"], hyb)
o = C.options("**Example 2.**")
ok(o["B"] == "sp², sp², sp" and o["A"] == "sp³, sp², sp" and o["D"] == "sp², sp², sp²")
ok(sum(len(v) for v in atoms.values()) == 8)  # sigma bonds counted twice: C-H x3 + 2 C-C + C-N
C.ok(C.key_letter(1) is not None)
C.textopt("**Example 2.**", "B", "sp², sp², sp")

# ---- Q1 highest boiling point
ok(max(["H2O", "H2S", "CH4", "HCl", "Ne"], key=lambda k: BP[k]) == "H2O")
C.textopt("**1.**", "A", "H₂O")
# ---- Q2 trigonal pyramidal among options
opts = {"A": ("B", ["F"] * 3), "B": ("C", ["H"] * 4), "C": ("N", ["H"] * 3), "D": ("C", ["O", "O"]), "E": ("S", ["O"] * 3)}
hits = [k for k, (c, l) in opts.items() if shape(c, l)[0] == "trigonal pyramidal"]
ok(hits == ["C"], hits)
C.textopt("**2.**", "C", "NH₃")
# ---- Q3 CO2
ok(HYB[steric("C", ["O", "O"])] == "sp" and shape("C", ["O", "O"])[0] == "linear")
C.textopt("**3.**", "E", "sp, linear")
# ---- Q4 H-bond donors: H bonded directly to N, O or F
mols = {"A": ["C-H"], "B": ["C-H", "O-H"], "C": ["C-H", "C-F"], "D": ["C-H", "C-O"], "E": ["C=O"]}
donors = [k for k, bonds in mols.items() if any(b in ("N-H", "O-H", "F-H") for b in bonds)]
ok(donors == ["B"])
C.textopt("**4.**", "B", "CH₃OH")
# ---- Q5 amphoteric oxide (facts)
OXIDE = {"Na2O": "basic", "CO2": "acidic", "SO3": "acidic", "Al2O3": "amphoteric", "MgO": "basic"}
ok([k for k, v in OXIDE.items() if v == "amphoteric"] == ["Al2O3"])
C.textopt("**5.**", "D", "Al₂O₃")
# the two balanced equations in the key
def atoms_count(side):
    from collections import Counter
    cnt = Counter()
    for coef, formula in side:
        for el, n in formula.items(): cnt[el] += coef * n
    return cnt
ok(atoms_count([(1, {"Al": 2, "O": 3}), (6, {"H": 1, "Cl": 1})]) == atoms_count([(2, {"Al": 1, "Cl": 3}), (3, {"H": 2, "O": 1})]))
ok(atoms_count([(1, {"Al": 2, "O": 3}), (2, {"Na": 1, "O": 1, "H": 1}), (3, {"H": 2, "O": 1})]) == atoms_count([(2, {"Na": 1, "Al": 1, "O": 4, "H": 4})]))
ok(atoms_count([(1, {"Na": 2, "O": 1}), (1, {"H": 2, "O": 1})]) == atoms_count([(2, {"Na": 1, "O": 1, "H": 1})]))
ok(atoms_count([(1, {"S": 1, "O": 3}), (1, {"H": 2, "O": 1})]) == atoms_count([(1, {"H": 2, "S": 1, "O": 4})]))
ok([C.key_letter(i) for i in range(1, 6)] == list("ACEBD"))
C.done()
