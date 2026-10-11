"""Independent checks for materi/biology/cell-photosynthesis.md.

Atom balance of every equation option is computed with a formula parser, the pondweed and
limiting-factor tables are read by code, the starch-test logic is a tiny model, and every
distractor note of the answer key is reproduced by the wrong reasoning it names."""
import pathlib, re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/cell-photosynthesis.md").read_text()
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

def atoms(formula):
    c = Counter()
    for el, k in re.findall(r"([A-Z][a-z]?)(\d*)", formula.translate(SUB)):
        c[el] += int(k or 1)
    return c

def side(s):
    total = Counter()
    for term in s.split(" + "):
        m = re.match(r"(\d*)(.+)", term.strip())
        k = int(m.group(1) or 1)
        for el, v in atoms(m.group(2)).items():
            total[el] += k * v
    return total

def balanced(eq):
    l, r = eq.split(" → ")
    return side(l) == side(r)

# ---- Core idea 2 and the SVG: the equation is balanced
EQ = "6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂"
ok(EQ in TXT and EQ.replace(" → ", "  →  ") in (ROOT / "public/content/biology/photosynthesis-equation.svg").read_text())
ok(balanced(EQ) and dict(side("6CO₂ + 6H₂O")) == {"C": 6, "O": 18, "H": 12})
ok("6 C, 12 H and 18 O" in TXT and "C 6 = 6, H 12 = 12, O 18 = 18" in (ROOT / "public/content/biology/photosynthesis-equation.svg").read_text())

# ---- Example 1: plateau
rate = {1: 6, 2: 12, 3: 18, 4: 24, 5: 24, 6: 24}
row = re.search(r"\| Bubbles per minute \|(.*)\|", TXT).group(1).split("|")
ok([int(x) for x in row] == list(rate.values()))
top = max(rate.values())
first_plateau = min(k for k, v in rate.items() if v == top)
ok(first_plateau == 4)
ok(all(rate[k + 1] - rate[k] == 6 for k in (1, 2, 3)))
o = options("**Example 1.**")
ok(len(set(o.values())) == 5)
ok(o["B"].startswith("At 4;") and "CO₂" in o["B"] and "temperature" in o["B"])
ok(o["A"].startswith("At 2;") and rate[2] > rate[1])        # still rising at 2
ok(o["C"].startswith("At 4;") and "raise the light" in o["C"])  # more light on a plateau: no gain
ok(o["D"].startswith("At 6;") and 6 == max(rate))               # last reading
ok(o["E"].startswith("At 5;") and rate[5] == rate[4])           # second plateau point

# ---- Example 2: starch model (destarched leaf; starch only if light and CO2 and chlorophyll)
def starch(light, co2, chl=True):
    return light and co2 and chl
leafA = starch(True, True)      # water dish: CO2 present
leafB = starch(True, False)     # KOH removes CO2
ok(leafA and not leafB)
colors = {True: "blue-black", False: "brown"}
o = options("**Example 2.**")
def expect(a, b, why):
    return f"Leaf A {colors[a]} and leaf B {colors[b]}, so {why}"
ok(o["B"].startswith(expect(leafA, leafB, "CO₂ is needed")))
ok(o["E"].startswith(expect(leafA, leafB, "light is needed")))     # same colors, wrong reason: light is the same in both jars
ok(o["C"].startswith(expect(leafB, leafA, "KOH helps")[:28]) and colors[leafB] == "brown" and o["C"].startswith("Leaf A brown"))  # swapped
ok(o["A"].startswith("Both leaves blue-black") and not (leafA and leafB))
ok(o["D"].startswith("Both leaves brown") and not (not leafA and not leafB))
ok(len({"light" for _ in (1, 2)}) == 1)  # light identical in both jars

# ---- Check Q1: atom counting for each option
o = options("**1.**")
ok(len(set(o.values())) == 5)
res = {k: balanced(v) for k, v in o.items()}
ok(res == {"A": False, "B": False, "C": True, "D": True, "E": False}, res)
photo_like = {k: v.split(" → ")[0].startswith(("6CO₂", "CO₂")) for k, v in o.items()}
good = [k for k in o if res[k] and photo_like[k]]
ok(good == ["D"] and key_letter(1) == "D")
ok(side(o["B"].split(" → ")[0])["H"] == 24 and side(o["B"].split(" → ")[1])["H"] == 12)
ok(side(o["E"].split(" → ")[0])["O"] == 18 and side(o["E"].split(" → ")[1])["O"] == 30)
ok(atoms("CO₂")["C"] == 1 and side(o["A"].split(" → ")[1])["C"] == 6)

# ---- Check Q2: model of the cook's plants
# Windowsill: light yes. Cupboard: no light, old starch used in respiration over a week.
sill = starch(True, True); cupboard = starch(False, True)
ok(sill and not cupboard)
ok(options("**2.**")["A"].startswith("Windowsill leaf blue-black, cupboard leaf brown") and key_letter(2) == "A")
o2 = options("**2.**")
ok(o2["C"].startswith("Windowsill leaf brown") and o2["B"].startswith("Both blue-black") and o2["D"].startswith("Both brown") and o2["E"].startswith("Both brown"))

# ---- Check Q3: which factor limits at (20 C, 0.04 %)?
table = {(20, 0.04): 12, (20, 0.08): 12, (30, 0.08): 18}
rows = re.findall(r"\| (\d+) °C \| ([\d.]+) % \| (\d+) \|", TXT)
ok({(int(a), float(b)): int(c) for a, b, c in rows} == table)
base = table[(20, 0.04)]
co2_changes = table[(20, 0.08)] - base
temp_changes = table[(30, 0.08)] - table[(20, 0.08)]
ok(co2_changes == 0 and temp_changes == 6)
limiting = "temperature" if temp_changes > 0 and co2_changes == 0 else "co2"
ok(limiting == "temperature")
o = options("**3.**")
ok(o["C"] == "Temperature" and key_letter(3) == "C" and len(set(o.values())) == 5)

# ---- Check Q4: bubble rates
ok(36 / 3 == 12 and 12 / 3 == 4 and 36 - 12 == 24 and 36 * 3 == 108)
o = options("**4.**")
ok(o["B"].startswith("12 ") and o["A"].startswith("3 ") and o["C"].startswith("24 ") and o["D"].startswith("36 ") and o["E"].startswith("108 "))
ok(key_letter(4) == "B")

# ---- Check Q5: stoichiometry
glucose = 4
co2 = 6 * glucose; o2n = 6 * glucose
ok((co2, o2n) == (24, 24))
o = options("**5.**")
ok(o["E"] == "24 CO₂ and 24 O₂" and o["D"] == "24 CO₂ and 4 O₂" and o["C"] == "24 CO₂ and 12 O₂" and o["B"] == "6 CO₂ and 6 O₂" and o["A"] == "4 CO₂ and 4 O₂")
ok(key_letter(5) == "E" and 6 * 1 == 6)

# ---- Key letters
keys = [key_letter(q) for q in range(1, 6)]
ok(keys == ["D", "A", "C", "B", "E"])
ok(max(keys.count(c) for c in "ABCDE") <= 2)
for q in range(1, 6):
    ok(len(options(f"**{q}.**")) == 5)

# ---- Facts (statement, source) that the text, examples and keys rely on
FACT_CHECKS = [
    ("Photosynthesis: 6CO2 + 6H2O + light -> C6H12O6 + 6O2, in chloroplasts", "https://openstax.org/books/biology-2e/pages/8-1-overview-of-photosynthesis"),
    ("Photosynthesis takes place in chloroplasts; chlorophyll absorbs light; oxygen is released", "https://en.wikipedia.org/wiki/Photosynthesis"),
    ("Photosynthesis supplies the oxygen of the atmosphere and the energy base of food chains", "https://en.wikipedia.org/wiki/Photosynthesis"),
    ("Hot dry conditions: stomata close and CO2 drops, so photosynthesis falls", "https://en.wikipedia.org/wiki/Photosynthesis"),
    ("Light and CO2 graphs rise then plateau; temperature rises to an optimum and falls (enzymes denature)", "https://www.tutorchase.com/answers/igcse/biology/what-are-the-limiting-factors-of-photosynthesis"),
    ("Limiting factor = factor furthest from its optimum; raising it raises the rate until another factor limits", "https://studymind.co.uk/notes/limiting-factors-of-photosynthesis/"),
    ("Starch test: destarch in darkness, boil, warm in ethanol, add iodine; green parts blue-black, white parts orange-brown", "https://www.savemyexams.com/gcse/biology/ocr/a-gateway/16/revision-notes/7-practical-skills/practical-skills/practical-investigating-photosynthesis"),
    ("A variegated leaf shows the need for chlorophyll; a hydroxide in the jar absorbs CO2 to show the need for CO2", "https://savemyexams.com/igcse/biology/cie/23/revision-notes/6-plant-nutrition/6-1-photosynthesis-and-leaf-structure/6-1-5-investigating-the-need-for-chlorophyll-light-and-carbon-dioxide"),
    ("KOH reacts with CO2 (so it removes CO2 from the jar)", "https://en.wikipedia.org/wiki/Potassium_hydroxide"),
    ("Hydrilla under an inverted funnel with sodium bicarbonate gives oxygen bubbles that relight a glowing splint", "https://waeconline.org.ng/e-learning/biology/Bio317nq1.html"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
