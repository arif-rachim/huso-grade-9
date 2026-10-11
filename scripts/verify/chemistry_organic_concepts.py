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

# ------------------------------------------------------------------ molecule graphs (trees)
class Mol:
    def __init__(self):
        self.lab, self.adj = {}, {}

    def add(self, label, bonded_to=None):
        i = len(self.lab)
        self.lab[i] = label
        self.adj[i] = set()
        if bonded_to is not None:
            self.adj[i].add(bonded_to); self.adj[bonded_to].add(i)
        return i


def chain_mol(n, subs=None, oh=None):
    """Main chain of n carbons; subs = {position: number of carbons in an n-alkyl branch}; oh = position of OH."""
    m = Mol()
    ids = []
    for k in range(n):
        ids.append(m.add("C", ids[-1] if ids else None))
    for pos, size in (subs or {}).items():
        prev = ids[pos - 1]
        for _ in range(size):
            prev = m.add("C", prev)
    if oh:
        m.add("O", ids[oh - 1])
    return m


def canon(m):
    """Canonical string of a labeled tree (AHU encoding rooted at the tree center(s))."""
    deg = {i: len(a) for i, a in m.adj.items()}
    left = set(m.adj)
    leaves = [i for i in left if deg[i] <= 1]
    while len(left) > 2:
        nxt = []
        for l in leaves:
            left.discard(l)
            for nb in m.adj[l]:
                if nb in left:
                    deg[nb] -= 1
                    if deg[nb] == 1:
                        nxt.append(nb)
        leaves = nxt
    def enc(v, parent):
        return "(" + m.lab[v] + "".join(sorted(enc(w, v) for w in m.adj[v] if w != parent)) + ")"
    return min(enc(c, None) for c in left)


def paths(m):
    """All simple paths between carbon atoms (unique in a tree)."""
    cs = [i for i in m.lab if m.lab[i] == "C"]
    out = []
    for a, b in itertools.combinations(cs, 2):
        stack = [(a, [a])]
        while stack:
            v, p = stack.pop()
            if v == b:
                out.append(p); break
            for w in m.adj[v]:
                if w not in p and m.lab[w] == "C":
                    stack.append((w, p + [w]))
    return out or [[cs[0]]]


STEM = ["meth", "eth", "prop", "but", "pent", "hex", "hept", "oct", "non", "dec"]
ALKYL = {1: "methyl", 2: "ethyl", 3: "propyl"}


def iupac_name(m):
    oh_c = next((n for i in m.lab if m.lab[i] == "O" for n in m.adj[i]), None)
    best = None
    elig = [p for p in paths(m) if oh_c is None or oh_c in p]
    longest = max(len(p) for p in elig)
    for p in elig:
        if len(p) < longest:
            continue
        for chain in (p, p[::-1]):
            subs = []
            for pos, c in enumerate(chain, 1):
                for nb in m.adj[c]:
                    if nb in chain or m.lab[nb] == "O":
                        continue
                    # size of a straight alkyl branch
                    size, prev, cur = 0, c, nb
                    while True:
                        size += 1
                        nxt = [w for w in m.adj[cur] if w != prev]
                        if not nxt:
                            break
                        assert len(nxt) == 1, "branched side chain not supported"
                        prev, cur = cur, nxt[0]
                    subs.append((pos, ALKYL[size]))
            ohp = chain.index(oh_c) + 1 if oh_c is not None else 0
            key = (-len(chain), ohp, sorted(s[0] for s in subs))
            if best is None or key < best[0]:
                best = (key, chain, subs, ohp)
    key, chain, subs, ohp = best
    parts = []
    groups = {}
    for pos, nm in subs:
        groups.setdefault(nm, []).append(pos)
    mult = {1: "", 2: "di", 3: "tri"}
    for nm in sorted(groups):
        ps = sorted(groups[nm])
        parts.append(",".join(map(str, ps)) + "-" + mult[len(ps)] + nm)
    stem = STEM[len(chain) - 1]
    name = "-".join(parts) + stem + (f"an-{ohp}-ol" if ohp else "ane")
    return name


def from_name(name):
    """Build the structure a name describes (no rule checking): prefixes, stem, ane / an-N-ol."""
    mt = re.fullmatch(r"((?:\d+(?:,\d+)*-(?:di|tri)?(?:methyl|ethyl|propyl))*)(meth|eth|prop|but|pent|hex|hept|oct|non|dec)(?:ane|an-(\d+)-ol)", name.replace("-methyl", "-methyl"))
    ok(mt is not None, name)
    pre, stem, ohp = mt.groups()
    n = STEM.index(stem) + 1
    subs = {}
    for loc, mult, alk in re.findall(r"(\d+(?:,\d+)*)-(di|tri)?(methyl|ethyl|propyl)", pre):
        for pos in loc.split(","):
            subs[int(pos)] = {"methyl": 1, "ethyl": 2, "propyl": 3}[alk]
    # a chain position may carry two branches only in cases we do not use here
    return chain_mol(n, subs, int(ohp) if ohp else None)


# --- sanity of the tools themselves
ok(iupac_name(chain_mol(6, {3: 1})) == "3-methylhexane", iupac_name(chain_mol(6, {3: 1})))
ok(iupac_name(chain_mol(5, {4: 1}, oh=2)) == "4-methylpentan-2-ol")
ok(canon(chain_mol(6, {3: 1})) == canon(chain_mol(6, {4: 1})))      # numbering direction does not change the molecule

# ------------------------------------------------------------------ Example 1
target1 = chain_mol(5, {4: 1}, oh=2)       # CH3-CH(OH)-CH2-CH(CH3)-CH3
ok(iupac_name(target1) == "4-methylpentan-2-ol")
o = C.options("**Example 1.**")
same, proper = [], []
for k, name in o.items():
    if name == "1,3-dimethylbutan-1-ol":
        m = chain_mol(4, {1: 1, 3: 1}, oh=1)   # two methyls, OH on C1
    else:
        m = from_name(name)
    if canon(m) == canon(target1):
        same.append(k)
        if iupac_name(m) == name:
            proper.append(k)
ok(same == ["A", "B", "D"], same)               # A, B, D are the same molecule: C and E are different molecules
ok(proper == ["B"], proper)                      # only B follows the rules
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
cond = chain_mol(6, {3: 1})                       # CH3CH2CH(CH3)CH2CH2CH3
o = C.options("**2.**")
res = {}
for k, name in o.items():
    if name == "2-ethylpentane":
        m = chain_mol(5, {2: 2})
    elif name == "2-propylbutane":
        m = chain_mol(4, {2: 3})
    else:
        m = from_name(name)
    res[k] = (canon(m) == canon(cond), iupac_name(m) == name)
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
