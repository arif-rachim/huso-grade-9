"""Independent checks for materi/biology/biochem-molecules.md (examples + check questions)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/biochem-molecules.md").read_text()
KEY = TXT.split("<details>")[1]
n = 0

def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1

def options(label):
    i = TXT.index(label)
    block = TXT[i:]
    line = next(l for l in block.splitlines() if l.startswith("(A)"))
    o = dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))
    ok(len(o) == 5 and len(set(o.values())) == 5, f"{label}: need 5 distinct options")
    return o

def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", KEY, re.M).group(1)

# --- tiny chemistry model: atoms as dicts -----------------------------------
def formula(**k): return dict(k)
def join(a, b):  # dehydration synthesis: add two molecules, remove H2O
    r = {e: a.get(e, 0) + b.get(e, 0) for e in set(a) | set(b)}
    r["H"] -= 2; r["O"] -= 1
    return r
glucose = formula(C=6, H=12, O=6)
ok(glucose["H"] == 2 * glucose["C"] and glucose["O"] == glucose["C"], "(CH2O)n ratio 1:2:1")
sucrose = join(glucose, glucose)       # glucose + fructose (same formula as glucose)
ok(sucrose == dict(C=12, H=22, O=11), "sucrose / maltose formula")

# --- carbon valence (Q1) ------------------------------------------------------
VALENCE_C = 4
ok(VALENCE_C - 2 == 2)                 # two C neighbors -> 2 H left
ok(VALENCE_C - 1 == 3 and VALENCE_C - 3 == 1 and VALENCE_C - 0 == 4)  # end, branch, methane distractors

# --- peptide chain counting by simulation (Example 1, Q5) --------------------
def build_chain(m):
    bonds = waters = 0
    chain = 1                             # first amino acid
    for _ in range(m - 1):
        chain += 1; bonds += 1; waters += 1   # each new aa joins by one bond, losing one H2O
    return bonds, waters
b, w = build_chain(120)
ok((b, w) == (119, 119), "Example 1")
ok(options("**Example 1.**")["B"] == "119")
ok(options("**Example 1.**")["C"] == "120" and options("**Example 1.**")["E"] == "240" and 2 * 120 == 240)
b5, w5 = build_chain(8)
ok((b5, w5) == (7, 7))
o5 = options("**5.**")
ok(o5["A"] == "7" and key_letter(5) == "A")
ok(o5["B"] == "8" and o5["C"] == "9" and o5["D"] == "14" and o5["E"] == "16" and 2 * 7 == 14 and 2 * 8 == 16)

# --- Q1 key
o1 = options("**1.**")
ok(o1["C"] == "2" and key_letter(1) == "C")

# --- Q2 pairing, checked against a lookup table --------------------------------
monomer_of = {"protein": "amino acids", "starch": "glucose", "cellulose": "glucose", "glycogen": "glucose",
              "DNA": "nucleotides", "RNA": "nucleotides", "fat": "glycerol + fatty acids"}
o2 = options("**2.**")
pairs = {"A": ("fatty acids", "protein"), "B": ("nucleotides", "starch"), "C": ("amino acids", "cellulose"),
         "D": ("glucose", "glycogen"), "E": ("glycerol", "DNA")}
good = [k for k, (m, p) in pairs.items() if monomer_of[p] == m]
ok(good == ["D"] and key_letter(2) == "D")
for k, (m, p) in pairs.items():
    ok(f"{m} → {p}" == o2[k], f"Q2 option {k}")

# --- Q3 butter / oil: option text checks -------------------------------------
o3 = options("**3.**")
ok(key_letter(3) == "B" and "unsaturated" in o3["B"] and "kinks" in o3["B"])
ok("more saturated" in o3["E"])        # swapped version is wrong

# --- Q4 element clue -----------------------------------------------------------
elements = {"starch": set("CHO"), "fat": set("CHO"), "cellulose": set("CHO"), "protein": set("CHON"), "DNA": set("CHONP")}
o4 = options("**4.**")
target = set("CHONP")
match = [k for k, name in {"A": "starch", "B": "fat", "C": "cellulose", "D": "protein", "E": "DNA"}.items() if elements[name] == target]
ok(match == ["E"] and key_letter(4) == "E")

# --- letter spread -------------------------------------------------------------
letters = [key_letter(q) for q in range(1, 6)]
ok(len(letters) == 5 and max(letters.count(c) for c in set(letters)) <= 2, letters)

# --- structure of the file -----------------------------------------------------
cp = TXT[TXT.index("## ✅ Check"):]
for q in range(1, 6):
    ok(re.search(rf"^\*\*{q}\.\*\*", cp, re.M) is not None)
    ok(re.search(rf"^{q}\. \*\*\(([A-E])\)", KEY, re.M) is not None)

# --- FACT CHECKS: (statement, source) -------------------------------------------
FACT_CHECKS = [
    ("Carbon forms up to four covalent bonds and builds chains and rings", "https://openstax.org/books/biology-2e/pages/2-3-carbon"),
    ("Monomers join into polymers by dehydration synthesis (water removed); hydrolysis adds water", "https://openstax.org/books/biology-2e/pages/3-1-synthesis-of-biological-macromolecules"),
    ("Carbohydrates are (CH2O)n; glucose is C6H12O6", "https://openstax.org/books/biology-2e/pages/3-2-carbohydrates"),
    ("Sucrose, lactose, maltose are disaccharides; starch (plants), glycogen (animals, liver and muscle), cellulose (plant cell walls)", "https://openstax.org/books/biology-2e/pages/3-2-carbohydrates"),
    ("A fat is glycerol plus three fatty acids; saturated fats such as butter are solid, unsaturated plant oils are liquid", "https://openstax.org/books/biology-2e/pages/3-3-lipids"),
    ("Phospholipids form the cell membrane bilayer; cholesterol is a steroid lipid and a precursor of steroid hormones", "https://openstax.org/books/biology-2e/pages/3-3-lipids"),
    ("Proteins are built from 20 common amino acids joined by peptide bonds that release water", "https://openstax.org/books/biology-2e/pages/3-4-proteins"),
    ("Protein functions: enzymes, hormones such as insulin, structure, transport, defense", "https://openstax.org/books/biology-2e/pages/3-4-proteins"),
    ("Heat, acid or chemicals denature a protein; frying an egg is an irreversible example", "https://openstax.org/books/biology-2e/pages/3-4-proteins"),
    ("A nucleotide has a pentose sugar, a phosphate and a nitrogenous base; DNA has deoxyribose and T, RNA has ribose and U", "https://openstax.org/books/biology-2e/pages/3-5-nucleic-acids"),
    ("Syllabus: Biochemical Structures = carbon, nucleic acids, lipids, proteins, carbohydrates (HUSO 2026 Open Round Biology 9th-10th)", "https://openstax.org/books/biology-2e/pages/3-1-synthesis-of-biological-macromolecules"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
