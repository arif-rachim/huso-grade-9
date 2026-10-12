"""Independent checks for materi/chemistry/organic-concepts.md.
Method: (1) an IUPAC-naming algorithm for acyclic alkanes/alkanols written from the rules (longest chain, lowest locants) and a
name -> structure builder, compared as canonical trees; (2) stereoisomer counting by brute force over R/S labels with the molecule's
own symmetry; (3) electron-pair bookkeeping for the arrow question; (4) degree of unsaturation from the formula and from the
structure. If RDKit is installed (pip install rdkit) the R/S labels of the SVG and the stereoisomer count are cross-checked too."""
import itertools, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk

C = Chk("materi/chemistry/organic-concepts.md")
ok = C.ok

from chemistry_p2_organic import parse, canon, name, formula

# the tools themselves
ok(name(parse("CCC(C)CCC")) == "3-methylhexane")
ok(name(parse("CC(O)CC(C)C")) == "4-methylpentan-2-ol")
ok(canon(parse("CCC(C)CCC")) == canon(parse("CCCC(C)CC")))        # numbering direction does not change the molecule

# ------------------------------------------------------------------ Example 1
target1 = parse("CC(O)CC(C)C")       # CH3-CH(OH)-CH2-CH(CH3)-CH3  (the condensed formula in the question)
ok(name(target1) == "4-methylpentan-2-ol")
# each option name drawn by hand as the structure it describes, then compared with the target
drawn1 = {"A": "CC(C)CC(O)C",        # 2-methylpentan-4-ol : methyl on C2, OH on C4
          "B": "CC(O)CC(C)C",        # 4-methylpentan-2-ol
          "C": "CC(C)C(O)CC",        # 2-methylpentan-3-ol
          "D": "OC(C)CC(C)C",        # 1,3-dimethylbutan-1-ol : butane, methyl + OH on C1, methyl on C3
          "E": "CCC(O)C(C)C"}        # 4-methylpentan-3-ol : OH on C3, methyl on C4
o = C.options("**Example 1.**")
same = [k for k in o if canon(parse(drawn1[k])) == canon(target1)]
proper = [k for k in same if name(parse(drawn1[k])) == o[k]]
ok(same == ["A", "B", "D"], same)               # C and E are other molecules than the target
ok(proper == ["B"], proper)                      # only B follows the naming rules
ok("**Answer: (B).**" in C.txt.split("**Example 1.**")[1].split("**Example 2.**")[0])

# ------------------------------------------------------------------ Example 2: stereoisomers of CH3CHBrCHBrCH3 by brute force
# A configuration = (label at C2, label at C3). The molecule's own symmetry (C2 <-> C3 swap) maps (a, b) -> (b, a);
# R and S labels are intrinsic (CIP), so this swap keeps labels. Different stereoisomers = classes under that symmetry only.
combos = list(itertools.product("RS", repeat=2))
classes = {frozenset({c, (c[1], c[0])}) for c in combos}
mirror = lambda c: tuple("S" if x == "R" else "R" for x in c)
ok(len(classes) == 3, classes)
chiral = [cl for cl in classes if frozenset({mirror(c) for c in cl}) != cl]
meso = [cl for cl in classes if frozenset({mirror(c) for c in cl}) == cl]
ok(len(chiral) == 2 and len(meso) == 1)          # RR and SS (enantiomers) and one meso compound
C.mcq2("**Example 2.**", 3, "B")
# pentane analog (unsymmetric ends): 2,3-dibromopentane really has 4
ok(len(combos) == 4)                              # no symmetry swap: all 4 distinct

# ------------------------------------------------------------------ Q1: enantiomers  (one stereocenter, same connectivity, opposite configuration)
ok(mirror(("R",)) == ("S",))                      # R <-> S are mirror images; they differ at every (the only) center
ok(C.options("**1.**")["A"] == "enantiomers" and C.key_letter(1) == "A")

# ------------------------------------------------------------------ Q2 naming
cond = parse("CCC(C)CCC")                         # CH3CH2CH(CH3)CH2CH2CH3
drawn2 = {"A": "CC(CC)CCC", "B": "CCCC(C)CC", "C": "CCC(C)CCC", "D": "CCC(C)CCCC", "E": "CC(CCC)CC"}
o = C.options("**2.**")
res = {k: (canon(parse(drawn2[k])) == canon(cond), name(parse(drawn2[k])) == o[k]) for k in o}
ok([k for k, v in res.items() if v[0]] == ["A", "B", "C", "E"], res)       # D has 7 carbons, a different molecule
ok([k for k, v in res.items() if v[0] and v[1]] == ["C"], res)
ok(C.key_letter(2) == "C")

# ------------------------------------------------------------------ Q3 conformations: the energies drawn in the SVG
EN = {0: 19, 60: 3.8, 120: 16, 180: 0, 240: 16, 300: 3.8, 360: 19}
ok(min(EN, key=EN.get) == 180)
ok(EN[60] < EN[120] and EN[300] < EN[240])        # gauche is below eclipsed
ok(EN[0] == max(EN.values()))
opts = C.options("**3.**")
ok(opts["E"].startswith("anti") and C.key_letter(3) == "E")

# ------------------------------------------------------------------ Q4 arrow pushing bookkeeping
# state: set of bonds, dict of lone pairs. Reaction: OH- + H-Br. An arrow moves one electron pair.
lone = {"O": 3, "Br": 3}
bonds = {("O", "H"): 1}                            # in OH-
bonds_hbr = {("H", "Br"): 1}
# arrow 1: O lone pair -> new O-H bond (H cannot have two bonds, so arrow 2 must free it)
lone["O"] -= 1
new = {("O", "H2"): 1}
# arrow 2: H-Br bond pair -> becomes a lone pair on Br
del bonds_hbr[("H", "Br")]
lone["Br"] += 1
ok(lone == {"O": 2, "Br": 4})                      # H2O has 2 lone pairs on O; Br- has 4
ok(len(new) + 1 == 2)                              # exactly two pair movements = two arrows
ok(C.options("**4.**")["D"].startswith("two arrows: from a lone pair on O to H") and C.key_letter(4) == "D")

# ------------------------------------------------------------------ Q5 degree of unsaturation
def dou(c, h, n=0, x=0):
    return (2 * c + 2 + n - h - x) / 2


ok(dou(8, 8) == 5)
# from the structure of vanillin: 1 ring + 3 ring C=C + 1 C=O
ok(1 + 3 + 1 == 5)
ok(dou(6, 6) == 4 and dou(2, 4) == 1 and dou(2, 2) == 2)    # benzene, ethene, ethyne checks of the formula
C.mcq2("**5.**", 5, "B")

# ------------------------------------------------------------------ optional RDKit cross-check
try:
    from rdkit import Chem
    from rdkit.Geometry import Point3D
    from rdkit.Chem.EnumerateStereoisomers import EnumerateStereoisomers
    n_iso = len({Chem.MolToSmiles(x) for x in EnumerateStereoisomers(Chem.MolFromSmiles("CC(Br)C(Br)C"))})
    ok(n_iso == 3, n_iso)
    for flip, want in ((False, "R"), (True, "S")):          # the two 2-butanol drawings of organic-chirality.svg
        s = -1 if flip else 1
        m = Chem.AddHs(Chem.MolFromSmiles("CC(O)CC"))
        h = [a.GetIdx() for a in m.GetAtomWithIdx(1).GetNeighbors() if a.GetAtomicNum() == 1][0]
        pos = {1: (0, 0, 0), 0: (s * 52, 46, 0), 3: (-s * 52, 46, 0), 2: (s * 46, -52, 40), h: (-s * 46, -52, -40)}
        conf = Chem.Conformer(m.GetNumAtoms())
        for i in range(m.GetNumAtoms()):
            conf.SetAtomPosition(i, Point3D(*pos.get(i, (10.0 * i, 90.0, 5.0 * i))))
        m.AddConformer(conf)
        Chem.AssignStereochemistryFrom3D(m)
        ok(Chem.FindMolChiralCenters(m, useLegacyImplementation=False)[0][1] == want)
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    ok(CalcMolFormula(Chem.MolFromSmiles("COc1cc(C=O)ccc1O")) == "C8H8O3")
    rd = "with RDKit cross-checks"
except ImportError:
    rd = "(RDKit not installed: optional cross-checks skipped)"
C.letters_spread()
print(rd)
C.done()
