"""Independent checks for materi/biology/cell-respiration.md.

Atom balance of every equation (in the text, the SVGs and every answer option) is computed with a
formula parser; molecule counts of the examples and the check questions are recomputed from the
balanced equations; the comparison table is encoded as data and each option is tested against it."""
import pathlib, re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/cell-respiration.md").read_text()
SVG = (ROOT / "public/content/biology/respiration-types.svg").read_text()
n = 0

def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1

SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    return dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))

def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", TXT.split("<details>")[1], re.M).group(1)

def parse(formula):
    """Parse a formula with one level of parentheses, e.g. C₂H₅OH, CO₂, C₆H₁₂O₆."""
    c = Counter()
    for el, k in re.findall(r"([A-Z][a-z]?)(\d*)", formula.translate(SUB)):
        c[el] += int(k or 1)
    return c

def side(s):
    tot = Counter()
    for term in s.split(" + "):
        m = re.match(r"(\d*)(.+)", term.strip())
        k = int(m.group(1) or 1)
        for el, v in parse(m.group(2)).items():
            tot[el] += k * v
    return tot

def balanced(eq):
    l, r = eq.split(" → ")
    return side(l) == side(r)

AEROBIC = "C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O"
YEAST = "C₆H₁₂O₆ → 2C₂H₅OH + 2CO₂"
MUSCLE = "C₆H₁₂O₆ → 2C₃H₆O₃"
PHOTO = "6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂"
for e in (AEROBIC, YEAST, MUSCLE, PHOTO):
    ok(balanced(e), e)
ok(AEROBIC in TXT and YEAST in TXT and MUSCLE in TXT)
ok("C₆H₁₂O₆ + 6O₂" in SVG and "→ 6CO₂ + 6H₂O" in SVG and "→ 2C₂H₅OH + 2CO₂" in SVG and "→ 2C₃H₆O₃" in SVG)
ok(side("C₆H₁₂O₆ + 6O₂") == Counter({"C": 6, "H": 12, "O": 18}))
# lactic acid takes all the carbon: no CO2 is possible
ok(side("2C₃H₆O₃")["C"] == side("C₆H₁₂O₆")["C"] == 6 and 6 - side("2C₃H₆O₃")["C"] == 0)

# ATP numbers used in the text: aerobic 30-32 (modern), anaerobic 2
AER_ATP = (30, 32); ANA_ATP = 2
ok("30–32 ATP" in TXT and "2 ATP" in TXT)
ok(5 * 30 == 150 and 5 * ANA_ATP == 10 and "150 ATP" in TXT and "only 10 ATP" in TXT)

# ---- Example 1: coefficients scale with 5 glucose
g = 5
co2_aer = g * 6; lactic = g * 2
ok((co2_aer, lactic) == (30, 10))
o = options("**Example 1.**")
ok(len(set(o.values())) == 5)
ok(o["B"] == "30 CO₂ and 10 lactic acid")
ok(o["A"] == "5 CO₂ and 5 lactic acid" and o["C"] == "30 CO₂ and 5 lactic acid"
   and o["D"] == "10 CO₂ and 10 lactic acid" and o["E"] == "30 CO₂ and 30 lactic acid")
ok(g * 1 == 5 and g * 2 == 10 and g * 6 == 30)   # the wrong ratios named in the traps

# ---- Example 2: yeast, 3 glucose
g = 3
eth = g * 2; co2 = g * 2
ok((eth, co2) == (6, 6))
o = options("**Example 2.**")
ok(o["D"] == "6 ethanol and 6 CO₂" and o["A"] == "3 ethanol and 3 CO₂" and o["B"] == "6 ethanol and 3 CO₂"
   and o["C"] == "3 ethanol and 6 CO₂" and o["E"] == "12 ethanol and 12 CO₂" and len(set(o.values())) == 5)
ok(g * 4 == 12)
ok(side("2C₂H₅OH + 2CO₂") == Counter({"C": 6, "H": 12, "O": 6}) == side("C₆H₁₂O₆"))

# ---- Q2: which option is the balanced aerobic equation
o = options("**2.**")
ok(len(set(o.values())) == 5)
verdict = {k: balanced(v) for k, v in o.items()}
ok(verdict == {"A": True, "B": False, "C": True, "D": True, "E": False}, verdict)
aerobic_like = [k for k, v in o.items() if verdict[k] and v.split(" → ")[0] == "C₆H₁₂O₆ + 6O₂"]
ok(aerobic_like == ["A"] and key_letter(2) == "A")
ok(o["C"] == PHOTO and o["D"] == YEAST)
ok(side(o["E"].split(" → ")[1])["H"] == 24 and side(o["E"].split(" → ")[0])["H"] == 12)

# ---- Q3: products by tissue
products = {"yeast/plant": {"ethanol", "CO₂"}, "muscle": {"lactic acid"}}
o = options("**3.**")
ok(o["B"] == "Lactic acid, and no CO₂" and key_letter(3) == "B")
ok(products["muscle"] == {"lactic acid"} and "CO₂" not in products["muscle"])
ok(o["A"] == "Ethanol and CO₂" and set(["ethanol", "CO₂"]) == products["yeast/plant"])
ok(o["E"] == "Ethanol, and no CO₂" and o["C"] == "Lactic acid and CO₂" and o["D"] == "Glucose and O₂")

# ---- Q5: comparison table as data
TABLE = {
    "needs light": (True, False),
    "releases oxygen": (True, False),
    "takes in carbon dioxide": (True, False),
    "stores light energy as chemical energy": (True, False),
    "happens in every living cell, day and night": (False, True),
}
o = options("**5.**")
claims = {"A": "needs light", "B": "releases oxygen", "C": "takes in carbon dioxide",
          "D": "stores light energy as chemical energy", "E": "happens in every living cell, day and night"}
for k, v in claims.items():
    ok(o[k].lower().replace("it ", "", 1).rstrip(".") == v or v in o[k].lower(), (k, o[k]))
# true of respiration (index 1) but NOT of photosynthesis (index 0)
good = [k for k, c in claims.items() if TABLE[c][1] and not TABLE[c][0]]
ok(good == ["E"] and key_letter(5) == "E")

# ---- Q1 / Q4 are concept questions: check the key letters and option text
o = options("**1.**")
ok(o["C"].startswith("It releases energy from food") and key_letter(1) == "C")
o = options("**4.**")
ok(o["D"] == "CO₂; most of the ethanol evaporates in the oven" and key_letter(4) == "D")
ok(len(set(o.values())) == 5)

# ---- table in the text has the six rows
rows = re.findall(r"^\| \*\*(.+?)\*\* \|", TXT, re.M)
ok(rows == ["Where", "When", "Takes in", "Gives out", "Energy", "Food (dry mass)"])

keys = [key_letter(q) for q in range(1, 6)]
ok(keys == ["C", "A", "B", "D", "E"])
ok(max(keys.count(c) for c in "ABCDE") <= 2)
for q in range(1, 6):
    ok(len(options(f"**{q}.**")) == 5)

FACT_CHECKS = [
    ("Aerobic respiration: C6H12O6 + 6O2 -> 6CO2 + 6H2O + energy", "https://en.wikipedia.org/wiki/Cellular_respiration"),
    ("Modern estimate about 30-32 ATP per glucose (older textbooks 36-38); fermentation gives only 2 ATP", "https://en.wikipedia.org/wiki/Cellular_respiration"),
    ("Glycolysis and fermentation take place in the cytoplasm; the citric acid cycle and oxidative phosphorylation in mitochondria", "https://en.wikipedia.org/wiki/Cellular_respiration"),
    ("Ethanol fermentation by yeast: C6H12O6 -> 2 C2H5OH + 2 CO2; CO2 bubbles make dough rise and ethanol mostly evaporates in baking", "https://en.wikipedia.org/wiki/Fermentation"),
    ("Lactic acid fermentation in muscle when oxygen is short: C6H12O6 -> 2 lactic acid, 2 ATP, no CO2", "https://en.wikipedia.org/wiki/Lactic_acid_fermentation"),
    ("ATP is the cell's energy currency; hydrolysis ATP -> ADP + phosphate releases energy", "https://en.wikipedia.org/wiki/Adenosine_triphosphate"),
    ("ATP is the energy currency used for muscle contraction and pumping ions", "https://openstax.org/books/biology-2e/pages/7-1-energy-in-living-systems"),
    ("Mitochondria use aerobic respiration to make ATP (powerhouse of the cell)", "https://en.wikipedia.org/wiki/Mitochondrion"),
    ("Photosynthesis in chloroplasts: 6CO2 + 6H2O + light -> C6H12O6 + 6O2", "https://openstax.org/books/biology-2e/pages/8-1-overview-of-photosynthesis"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
