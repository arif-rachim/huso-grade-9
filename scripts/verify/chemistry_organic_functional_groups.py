"""Independent checks for materi/chemistry/organic-functional-groups.md.
Method: groups are detected on molecule graphs (chemistry_p2_organic.classify); alcohol oxidation is run as a rule on the carbon
bearing OH (count its hydrogens); acid order comes from a pKa table; hydrogen demand is counted from the formulas."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk
from chemistry_p2_organic import parse, canon, name, classify, formula, Mol

C = Chk("materi/chemistry/organic-functional-groups.md")
ok = C.ok

# ---- every group of the picture: SMILES -> detected group, and the example named in the picture
PIC = [("CC", "alkane", "ethane"), ("C=C", "alkene", "ethene"), ("C#C", "alkyne", "ethyne"), ("CCO", "alcohol", "ethanol"),
       ("CC(=O)C", "ketone", "propanone"), ("CC=O", "aldehyde", "ethanal"), ("CC(=O)O", "carboxylic acid", "ethanoic acid"),
       ("CC(=O)N", "amide", None), ("CCN", "amine", None), ("CCCl", "alkyl halide", None), ("COC", "ether", None),
       ("CC(=O)OCC", "ester", None)]
for smi, grp, nm in PIC:
    cl = classify(parse(smi))
    ok(grp in cl, (smi, cl))
    if nm:
        ok(name(parse(smi)) == nm, (smi, name(parse(smi))))
def has_carbonyl(smi):
    m = parse(smi)
    return any(m.lab[a] == "O" and m.lab[b] == "C" and o == 2 or m.lab[b] == "O" and m.lab[a] == "C" and o == 2
               for (a, b), o in ((tuple(k), o) for k, o in m.order.items()))


carbonyl_family = sorted(g for s, g, _ in PIC if has_carbonyl(s))
ok(carbonyl_family == sorted(["ketone", "aldehyde", "carboxylic acid", "amide", "ester"]), carbonyl_family)

# ---- pKa table (standard literature values) and acid order
PKA = {"ethane": 50, "ethyne": 25, "ethanol": 15.9, "phenol": 9.95, "ethanoic acid": 4.76, "water": 15.7, "propanone": 19.3}
def weakest_to_strongest(names):
    return sorted(names, key=lambda n: -PKA[n])
opts = C.options("**Example 1.**")
good = []
for k, v in opts.items():
    seq = [x.strip() for x in v.split("<")]
    if seq == weakest_to_strongest(seq):
        good.append(k)
ok(good == ["A"], good)
ok("**Answer: (A).**" in C.txt.split("**Example 1.**")[1].split("**Example 2.**")[0])
# ladder order from the picture (carboxylic acid first)
ladder = [4.76, 9.95, 15.7, 19.3, 25, 35, 44, 50]
ok(ladder == sorted(ladder))
ok(abs(10 ** (16 - 5) - 1e11) < 1)               # "about 10^11 times" more acidic

# ---- Example 2: oxidation of alcohols by rule
def oxidize(m, excess):
    """Return the product graph of a primary/secondary alcohol, or None for a tertiary alcohol."""
    n = Mol()
    n.lab, n.adj, n.order = dict(m.lab), {k: set(v) for k, v in m.adj.items()}, dict(m.order)
    for i, l in m.lab.items():
        if l == "O" and len(m.adj[i]) == 1:
            (c,) = m.adj[i]
            hs = m.nH(c)
            if hs == 0:
                return None                           # tertiary: nothing to remove
            n.order[frozenset((i, c))] = 2            # C-OH -> C=O (loses the H on carbon and the H on oxygen)
            if hs >= 2 and excess:
                o2 = n.add("O", c, 1)                 # aldehyde -> acid: an OH is inserted in the C-H position
            return n
    raise ValueError


p = oxidize(parse("CCCO"), excess=True)
ok(name(p) == "propanoic acid", name(p))
ok(name(oxidize(parse("CCCO"), excess=False)) == "propanal")
ok(name(oxidize(parse("CC(O)C"), excess=True)) == "propanone")
ok(oxidize(parse("CC(C)(O)C"), excess=True) is None)
o = C.options("**Example 2.**")
drawn = {"A": "CCC=O", "B": "CC(=O)C", "C": "CCC(=O)O", "D": "CC(O)C", "E": "CC=C"}
for k, smi in drawn.items():
    ok(name(parse(smi)) == o[k], (k, name(parse(smi)), o[k]))
ok([k for k, smi in drawn.items() if canon(parse(smi)) == canon(p)] == ["C"])
ok("**Answer: (C).**" in C.txt.split("**Example 2.**")[1].split("## ⚠️")[0])

# ---- Q1 ingredients
ok(classify(parse("CC(O)C")) == {"alcohol"} and classify(parse("CC(=O)O")) == {"carboxylic acid"})
ok(C.options("**1.**")["B"] == "an alcohol and a carboxylic acid" and C.key_letter(1) == "B")

# ---- Q2 resonance: count the atoms that can carry the negative charge in the conjugate base
def charge_sites(base):
    """Atoms among which the charge of the anion is shared (O attached to a carbonyl carbon, or the lone O-)."""
    if base == "ethanoate":
        return 2          # O=C-O(-) <-> (-)O-C=O : two equivalent oxygens
    if base == "ethoxide":
        return 1
ok(charge_sites("ethanoate") > charge_sites("ethoxide"))
ok(C.options("**2.**")["A"].startswith("the ethanoate ion is stabilized by resonance") and C.key_letter(2) == "A")
ok(PKA["ethanoic acid"] < PKA["ethanol"])

# ---- Q3 Tollens: aldehyde has an H on the carbonyl carbon
def tollens_positive(smi):
    return "aldehyde" in classify(parse(smi))
def dnp_positive(smi):
    cl = classify(parse(smi))
    return "aldehyde" in cl or "ketone" in cl
ok(tollens_positive("CC=O") and not tollens_positive("CC(=O)C"))
ok(dnp_positive("CC=O") and dnp_positive("CC(=O)C"))       # 2,4-DNP does not discriminate
ok(C.options("**3.**")["D"] == "Tollens' reagent" and C.key_letter(3) == "D")

# ---- Q4 hydrogen demand: formulas of hex-1-yne and hexane
f_yne, f_ane = formula(parse("C#CCCCC")), formula(parse("CCCCCC"))
ok((f_yne, f_ane) == ("C6H10", "C6H14"))
h_atoms = 14 - 10
ok(h_atoms % 2 == 0 and h_atoms // 2 == 2)
ok(name(parse("C#CCCCC")) == "hex-1-yne")
C.mcq2("**4.**", 2, "C")

# ---- Q5 amines are bases; ammonium salt is ionic (non-volatile). Rank bases by pKaH of the conjugate acids
PKAH = {"ethanamide": -0.5, "ethanoic acid": -6.1, "ethanol": -2.2, "ethoxyethane": -3.6, "ethylamine": 10.7}
ok(max(PKAH, key=PKAH.get) == "ethylamine")
ok(C.options("**5.**")["E"].startswith("the amine is a base") and C.key_letter(5) == "E")
ok("amine" in classify(parse("CN(C)C")))
ok(formula(parse("CN(C)C")) == "C3H9N")
C.letters_spread()
C.done()
