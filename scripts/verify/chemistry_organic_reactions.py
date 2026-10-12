"""Independent checks for materi/chemistry/organic-reactions.md.
Method: the reactions are carried out on molecule graphs (chemistry_p2_organic): Markovnikov addition by comparing carbocation
substitution, Zaitsev elimination by listing every beta-hydrogen, SN2 inversion by permuting the neighbors of a stereocenter and
re-reading the CIP label, rate laws by counting the molecules in the slow step. RDKit cross-checks run when it is installed."""
import itertools, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk
from chemistry_p2_organic import parse, canon, name, classify, formula, Mol

C = Chk("materi/chemistry/organic-reactions.md")
ok = C.ok


def copy(m):
    n = Mol()
    n.lab, n.adj, n.order = dict(m.lab), {k: set(v) for k, v in m.adj.items()}, dict(m.order)
    return n


def cc_double_bonds(m):
    return [tuple(k) for k, o in m.order.items() if o == 2 and all(m.lab[x] == "C" for x in k)]


def n_carbons_on(m, c, ignore=()):
    return sum(1 for x in m.adj[c] if m.lab[x] == "C" and x not in ignore)


# ------------------------------------------------------------------ Example 1: HBr + 2-methylbut-2-ene
alkene = parse("CC(C)=CC")
ok(name(alkene) == "2-methylbut-2-ene")
(a, b), = cc_double_bonds(alkene)
# protonating one carbon leaves the cation on the other: rate of that route ~ stability = number of carbon neighbors of the cation carbon
cation_subst = {a: n_carbons_on(alkene, a, ignore=(b,)) + 1, b: n_carbons_on(alkene, b, ignore=(a,)) + 1}   # +1: the former partner carbon
cation = max(cation_subst, key=cation_subst.get)
ok(sorted(cation_subst.values()) == [2, 3], cation_subst)          # secondary versus tertiary
ok(cation_subst[cation] == 3)
prod = copy(alkene)
prod.order[frozenset((a, b))] = 1
prod.add("Br", cation)
ok(name(prod) == "2-bromo-2-methylbutane", name(prod))
ok(formula(prod) == "C5H11Br")
drawn1 = {"A": "CC(Br)C(C)C", "B": "CC(C)(Br)CC", "C": "BrCC(C)CC", "D": "CC(C)(Br)C(Br)C", "E": "CC(C)(O)CC"}
o = C.options("**Example 1.**")
for k, smi in drawn1.items():
    ok(name(parse(smi)) == o[k], (k, name(parse(smi)), o[k]))
ok([k for k, smi in drawn1.items() if canon(parse(smi)) == canon(prod)] == ["B"])
ok(canon(parse(drawn1["A"])) != canon(prod))                       # anti-Markovnikov product (secondary C-Br)
ok("D" in drawn1 and formula(parse(drawn1["D"])) == "C5H10Br2")     # Br2 product has two Br
ok(classify(parse(drawn1["E"])) == {"alcohol"})
ok("**Answer: (B).**" in C.txt.split("**Example 1.**")[1].split("**Example 2.**")[0])

# ------------------------------------------------------------------ Example 2: SN2 inversion with CIP labels
# A stereocenter is a tuple of its four substituents in SMILES order: looking from the first, the other three run counterclockwise ('@').
def cip_label(neigh, rank):
    """neigh: tuple of 4 substituent names (SMILES '@' order); rank: name -> priority (1 highest)."""
    target = sorted(neigh, key=rank.get)           # (p1, p2, p3, p4)
    want = (target[3], target[0], target[1], target[2])    # looking from the lowest priority: 1, 2, 3 counterclockwise means R
    perm = [neigh.index(x) for x in want]
    inversions = sum(1 for i in range(4) for j in range(i + 1, 4) if perm[i] > perm[j])
    return "R" if inversions % 2 == 0 else "S"      # even permutation keeps '@' = counterclockwise from the lowest = R


# (R)-2-bromobutane, written in one of the two orders that give R
rank_br = {"Br": 1, "Et": 2, "Me": 3, "H": 4}
for cand in itertools.permutations(("Br", "Et", "Me", "H")):
    if cand[0] == "Me" and cip_label(cand, rank_br) == "R":
        start = cand
        break
ok(cip_label(start, rank_br) == "R")
# SN2: iodide enters opposite to Br; geometrically = I takes Br's slot and the other three flip (swap two of them)
def sn2(neigh, leaving, nucleophile):
    n = list(neigh)
    i = n.index(leaving)
    n[i] = nucleophile
    others = [j for j in range(4) if j != i]
    n[others[0]], n[others[1]] = n[others[1]], n[others[0]]      # umbrella flip = inversion
    return tuple(n)


def retention(neigh, leaving, nucleophile):
    return tuple(nucleophile if x == leaving else x for x in neigh)


rank_i = {"I": 1, "Et": 2, "Me": 3, "H": 4}
inv = sn2(start, "Br", "I")
ret = retention(start, "Br", "I")
ok(cip_label(inv, rank_i) == "S" and cip_label(ret, rank_i) == "R")
labels_sn1 = {cip_label(retention(start, "Br", "I"), rank_i), cip_label(sn2(start, "Br", "I"), rank_i)}
ok(labels_sn1 == {"R", "S"})                       # SN1: attack from either face gives both
opts = C.options("**Example 2.**")
ok(opts["B"] == "(S)-2-iodobutane" and opts["A"] == "(R)-2-iodobutane" and opts["C"].startswith("a 1 : 1 mixture"))
ok(name(parse("CC=CC")) == "but-2-ene" and opts["D"] == "but-2-ene")
ok(name(parse("CCCCI")) == "1-iodobutane" and opts["E"] == "1-iodobutane")
ok("**Answer: (B).**" in C.txt.split("**Example 2.**")[1].split("## ⚠️")[0])
ok(name(parse("CC(I)CC")) == "2-iodobutane")

# ------------------------------------------------------------------ Q1: SN2 rate follows crowding at the carbon bearing the halogen
subs = {"A": "CC(C)(C)Br", "B": "CC(C)Br", "C": "CCBr", "D": "CBr"}
crowd = {}
for k, smi in subs.items():
    m = parse(smi)
    cx = next(n for i in m.lab if m.lab[i] == "Br" for n in m.adj[i])
    crowd[k] = n_carbons_on(m, cx)
ok(crowd == {"A": 3, "B": 2, "C": 1, "D": 0}, crowd)
ok(min(crowd, key=crowd.get) == "D" and C.key_letter(1) == "D")
ok(C.options("**1.**")["E"] == "all react at the same rate")

# ------------------------------------------------------------------ Q2: E2 of 2-bromo-2-methylbutane, Zaitsev
sub = parse("CC(C)(Br)CC")
cx = next(n for i in sub.lab if sub.lab[i] == "Br" for n in sub.adj[i])
brs = next(i for i in sub.lab if sub.lab[i] == "Br")
products = {}
for beta in sub.adj[cx]:
    if sub.lab[beta] != "C" or sub.nH(beta) == 0:
        continue
    p = copy(sub)
    del p.adj[brs]; p.adj[cx].discard(brs); del p.lab[brs]; del p.order[frozenset((cx, brs))]
    for v in p.adj.values():
        v.discard(brs)
    p.order[frozenset((cx, beta))] = 2
    products[canon(p)] = (p, n_carbons_on(p, cx, ignore=(beta,)) + n_carbons_on(p, beta, ignore=(cx,)))
ok(len(products) == 2)
best = max(products.values(), key=lambda t: t[1])
ok(name(best[0]) == "2-methylbut-2-ene" and best[1] == 3, (name(best[0]), best[1]))
others = [v for v in products.values() if v is not best]
ok(name(others[0][0]) == "2-methylbut-1-ene" and others[0][1] == 2)
drawn2 = {"A": "C=C(C)CC", "B": "C=CC(C)C", "C": "CC(C)(OCC)CC", "D": "CC(C)(O)CC", "E": "CC=C(C)C"}
o = C.options("**2.**")
for k in "ABDE":
    ok(name(parse(drawn2[k])) == o[k], (k, name(parse(drawn2[k])), o[k]))
ok(classify(parse(drawn2["C"])) == {"ether"} and o["C"] == "2-ethoxy-2-methylbutane")
ok(canon(parse(drawn2["E"])) == canon(best[0]) and C.key_letter(2) == "E")

# ------------------------------------------------------------------ Q3: rate laws from the slow step
mechs = {"SN1": {"slow_step": ["RX"], "after": ["Nu"]}, "SN2": {"slow_step": ["RX", "Nu"], "after": []}}
def rate_ratio(mech, factor_nu):
    return factor_nu if "Nu" in mechs[mech]["slow_step"] else 1
ok(rate_ratio("SN1", 3) == 1 and rate_ratio("SN2", 3) == 3)
# 'the leaving group leaves first, then any nucleophile walks in' = ionization before attack = SN1
ok(C.options("**3.**")["B"] == "SN1; the rate does not change" and C.key_letter(3) == "B")
ok(C.options("**3.**")["E"] == "E2; the rate triples")

# ------------------------------------------------------------------ Q4: reactivity toward Nu: category first, then crowding
cands = {"A": "CCC(=O)CC", "B": "CC(=O)C", "C": "CC=O", "D": "CC(C)C(=O)C(C)C", "E": "CC(=O)OCC"}
cat_rank = {"aldehyde": 0, "ketone": 1, "ester": 2}        # lower = more reactive
def reactivity_key(smi):
    m = parse(smi)
    cl = classify(m)
    cat = next(cat_rank[c] for c in cl if c in cat_rank)
    carbonyl = next(i for i in m.lab if m.lab[i] == "C" and any(m.lab[x] == "O" and m.bo(i, x) == 2 for x in m.adj[i]))
    crowd = sum(n_carbons_on(m, x, ignore=(carbonyl,)) for x in m.adj[carbonyl] if m.lab[x] == "C")   # branching on the alpha carbons
    return (cat, crowd, len([x for x in m.adj[carbonyl] if m.lab[x] == "C"]))
order = sorted(cands, key=lambda k: reactivity_key(cands[k]))
ok(order[0] == "C" and order[-1] == "E", order)
ok(name(parse(cands["C"])) == "ethanal" and C.options("**4.**")["C"] == "ethanal" and C.key_letter(4) == "C")
ok(name(parse(cands["A"])) == "pentan-3-one" and name(parse(cands["B"])) == "propanone")
ok(name(parse(cands["D"])) == "2,4-dimethylpentan-3-one")
ok(order.index("B") < order.index("A") < order.index("D"))      # propanone > pentan-3-one > the hindered ketone

# ------------------------------------------------------------------ Q5: bromine water test
oil_like = parse("CCCC=CCCC")                       # an unsaturated chain stands in for oil
alkane = parse("CCCCCCCC")
ok("alkene" in classify(oil_like) and "alkene" not in classify(alkane))
adds_br2 = lambda m: bool(cc_double_bonds(m))
ok(adds_br2(oil_like) and not adds_br2(alkane))
ok(C.options("**5.**")["A"].startswith("the oil has C=C bonds") and C.key_letter(5) == "A")

# ------------------------------------------------------------------ optional RDKit cross-check of the CIP model
try:
    from rdkit import Chem
    # neighbors in SMILES order for 'C[C@H](Br)CC': CH3, H, Br, CH2CH3
    smi_neigh = ("Me", "H", "Br", "Et")
    lab_mine = cip_label(smi_neigh, rank_br)
    lab_rd = Chem.FindMolChiralCenters(Chem.MolFromSmiles("C[C@H](Br)CC"), useLegacyImplementation=False)[0][1]
    ok(lab_mine == lab_rd, (lab_mine, lab_rd))
    lab_rd2 = Chem.FindMolChiralCenters(Chem.MolFromSmiles("C[C@@H](Br)CC"), useLegacyImplementation=False)[0][1]
    ok(lab_rd2 != lab_rd)
    # inversion by SN2 from C[C@H](Br)CC -> I enters in Br's slot with two others swapped
    prod = sn2(smi_neigh, "Br", "I")      # order of '@' neighbors in the product
    # write product SMILES in that order: neighbors Me, H, I, Et with swapped pair -> compare labels via RDKit
    mapping = {"Me": "C", "Et": "CC", "H": "[H]", "I": "I"}
    m2 = Chem.MolFromSmiles("[C@](" + ")(".join(mapping[x] for x in prod[:3]) + ")" + mapping[prod[3]])
    ok(m2 is not None)
    lab_prod_rd = Chem.FindMolChiralCenters(m2, useLegacyImplementation=False)[0][1]
    ok(lab_prod_rd == cip_label(prod, rank_i), (lab_prod_rd, cip_label(prod, rank_i)))
    rd = "with RDKit cross-checks"
except ImportError:
    rd = "(RDKit not installed: optional cross-checks skipped)"
C.letters_spread()
print(rd)
C.done()
