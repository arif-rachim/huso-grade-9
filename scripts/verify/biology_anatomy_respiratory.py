"""Independent checks for materi/biology/anatomy-respiratory.md (logic items + fact-check list)."""
import pathlib, re
from fractions import Fraction
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/anatomy-respiratory.md").read_text()
KEYBLOCK = TXT.split("<details>")[1]
n = 0


def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1


def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    o = dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))
    ok(list(o) == list("ABCDE") and len(set(o.values())) == 5, f"{label}: 5 distinct options")
    return o


def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", KEYBLOCK, re.M).group(1)


# ---- model ----------------------------------------------------------------------------------
AIRWAY = ["nose", "pharynx", "larynx", "trachea", "bronchi", "bronchioles", "alveoli"]
# the text states the same path
ok("**Nose → pharynx (throat) → larynx (voice box) → trachea (windpipe) → two bronchi → bronchioles → alveoli.**" in TXT)
core1 = TXT.split("1. **The path of air.**")[1].split("2. **Gas exchange")[0]
idx = [core1.index(w) for w in ["Nose", "pharynx", "larynx", "trachea", "bronchi", "bronchioles", "alveoli"]]
ok(idx == sorted(idx))
svg = (ROOT / "public/content/biology/respiratory-pathway.svg").read_text()
labs = re.findall(r'data-label="([^"]+)"', svg)
ok(set(AIRWAY) | {"lungs", "diaphragm"} <= set(labs), labs)
ys = {w: int(re.search(rf'<text x="(?:8|352)" y="(\d+)">{w}</text>', svg).group(1)) for w in ["Nose", "Pharynx", "Larynx"]}
ok(ys["Nose"] < ys["Pharynx"] < ys["Larynx"], ys)

# Boyle's law as a tiny model: P1*V1 = P2*V2 (closed space, constant temperature)
P_OUT = Fraction(101_325)           # Pa, outside air
def lung_pressure(volume_ratio):    # volume relative to resting; start at P_OUT
    return P_OUT / volume_ratio
def flow(volume_ratio):
    p = lung_pressure(volume_ratio)
    return "in" if p < P_OUT else ("out" if p > P_OUT else "none")
BIGGER, SMALLER = Fraction(21, 20), Fraction(19, 20)
ok(flow(BIGGER) == "in" and flow(SMALLER) == "out")
ok(lung_pressure(BIGGER) < P_OUT < lung_pressure(SMALLER))

# ---- Example 1 truth table ---------------------------------------------------------------------
def inhalation_row():
    diaphragm = "contracts"            # contracting a dome-shaped muscle flattens it -> chest deeper
    ribs = "up and out"
    volume = "increases"
    pressure = "decreases" if flow(BIGGER) == "in" else "increases"
    return f"{diaphragm}; {ribs}; {volume}; {pressure}"
def exhalation_row():
    return "relaxes; down and in; decreases; increases"
o = options("**Example 1.**")
ok([k for k, v in o.items() if v == inhalation_row()] == ["B"], inhalation_row())
ok(o["A"] == exhalation_row())                                  # trap A is exhalation
ok(o["C"].endswith("increases; increases"))                      # impossible: bigger volume, bigger pressure
ok(o["D"].startswith("relaxes") and o["E"].startswith("contracts; down and in"))
ok(re.search(r"\*\*Answer: \(B\)\.\*\*", TXT) is not None)

# ---- Example 2: what rises while holding the breath ----------------------------------------------------
# simple model: per minute a resting body uses ~250 mL O2 and makes ~200 mL CO2 (RQ 0.8); lungs hold ~ 3 L of air at 15 % O2
o2_start = Fraction(21, 100) * 3000
for minutes in (1,):
    o2_left = o2_start - 250 * minutes
    co2 = Fraction(4, 100) * 3000 + 200 * minutes
    ok(o2_left > 0)                         # oxygen is NOT zero after a minute
    ok(co2 / 3000 > Fraction(4, 100) + Fraction(1, 100))      # CO2 fraction clearly higher
o = options("**Example 2.**")
ok(o["B"] == "the carbon dioxide level rises" and re.search(r"\*\*Answer: \(B\)\.\*\*", TXT) is not None)

# ---- Q1 order -----------------------------------------------------------------------------------------------
o = options("**1.**")
seqs = {k: [s.strip() for s in v.split("→")] for k, v in o.items()}
ok([k for k, s in seqs.items() if s == AIRWAY] == ["B"] and key_letter(1) == "B")
ok(all(sorted(s) == sorted(AIRWAY) for s in seqs.values()))      # same organs, shuffled

# ---- Q2 exhalation -----------------------------------------------------------------------------------------------
o = options("**2.**")
ok(o["E"] == "The diaphragm relaxes and moves up, and the chest gets smaller." and key_letter(2) == "E")
ok(flow(SMALLER) == "out")
ok("no muscles" in TXT and "squeeze themselves" in o["D"])

# ---- Q3 air composition -------------------------------------------------------------------------------------------
IN = {"N2": Fraction(78), "O2": Fraction(21), "CO2": Fraction(4, 100)}
OUT = {"N2": Fraction(78), "O2": Fraction(16), "CO2": Fraction(4)}
ok(IN["CO2"] * 100 == OUT["CO2"])                       # 100 times more CO2
ok(IN["O2"] - OUT["O2"] == 5 and OUT["O2"] < IN["O2"])  # about 5 points of O2 used
ok(sum(IN.values()) <= 100 and sum(OUT.values()) <= 100)   # remaining ~1-6 % = argon, water vapor...
ok(100 - sum(IN.values()) < 1.0)                           # inhaled: only ~0.96 % other (argon etc.)
o = options("**3.**")
ok(o["C"].startswith("less oxygen, about 100 times more carbon dioxide, and more water vapor") and key_letter(3) == "C")
ok(OUT["O2"] > 0)       # so D ("no oxygen left") is false
ok(OUT["N2"] == IN["N2"])   # E false
for needle in ("21 %", "16 %", "0.04 %", "4 %", "78 %"):
    ok(needle.replace(" ", "") in (ROOT / "public/content/biology/respiratory-air.svg").read_text().replace(" ", "") or needle in TXT, needle)

# ---- Q4 numbers (mL, exact) ------------------------------------------------------------------------------------------
breath = 500
kept = breath * (IN["O2"] - OUT["O2"]) / 100
ok(kept == 25)
o = options("**4.**")
val = {k: int(re.match(r"\d+", v).group(0)) for k, v in o.items()}
ok([k for k, v in val.items() if v == kept] == ["A"] and key_letter(4) == "A")
ok(val["B"] == breath * OUT["O2"] / 100 and val["C"] == breath * IN["O2"] / 100 and val["D"] == breath / 2 and val["E"] == breath)

# ---- Q5 tissue respiration; balanced equation ----------------------------------------------------------------------------
def atoms(formula):
    c = Counter()
    for el, k in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        c[el] += int(k or 1)
    return c
def side(items):
    tot = Counter()
    for coef, f in items:
        for el, k in atoms(f).items():
            tot[el] += coef * k
    return tot
left = side([(1, "C6H12O6"), (6, "O2")])
right = side([(6, "CO2"), (6, "H2O")])
ok(left == right, (left, right))                       # C6H12O6 + 6 O2 -> 6 CO2 + 6 H2O
ok("glucose + oxygen → carbon dioxide + water + energy" in TXT)
o = options("**5.**")
ok(o["D"].startswith("a reaction in the mitochondria") and key_letter(5) == "D")

# ---- letters and themes ----------------------------------------------------------------------------------------------------
letters = [key_letter(q) for q in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in "ABCDE") and len(letters) == 5, letters)
ok(len(re.findall(r"^\d\. \*\*\(", KEYBLOCK, re.M)) == 5)
ok("🏊" in TXT.split("## ✅ Check")[1] and "🎮" in TXT.split("## ✅ Check")[1])
# figures name all three levels
s3 = (ROOT / "public/content/biology/respiratory-three-levels.svg").read_text()
ok("BREATHING" in s3 and "GAS EXCHANGE" in s3 and "TISSUE (CELLULAR) RESPIRATION" in s3)

FACT_CHECKS = [
    ("Airway order nose, pharynx, larynx, trachea (C-shaped rings), bronchi, bronchioles, alveoli; gas exchange only in the respiratory zone", "https://openstax.org/books/anatomy-and-physiology-2e/pages/22-1-organs-and-structures-of-the-respiratory-system"),
    ("Inhalation: diaphragm contracts and moves down, external intercostals lift ribs up and out, alveolar pressure falls below atmospheric", "https://openstax.org/books/anatomy-and-physiology-2e/pages/22-3-the-process-of-breathing"),
    ("Normal exhalation is passive: muscles relax, elastic recoil, chest volume falls, pressure rises", "https://openstax.org/books/anatomy-and-physiology-2e/pages/22-3-the-process-of-breathing"),
    ("Pressure and volume change in opposite directions in a closed space; diaphragm and intercostals expand the chest", "https://openstax.org/books/biology-2e/pages/39-3-breathing"),
    ("Inhaled air about 78 % N2 and 20.95 % O2; exhaled 13.6-16 % O2, 4.0-5.3 % CO2 (about 100 times more), 5-6 % water vapor", "https://en.wikipedia.org/wiki/Breathing"),
    ("Lungs do not inflate themselves; the diaphragm and rib muscles enlarge the chest", "https://en.wikipedia.org/wiki/Breathing"),
    ("About 480 million alveoli, wall 0.2-0.6 micrometers thin, wrapped in capillaries; O2 diffuses in, CO2 out", "https://en.wikipedia.org/wiki/Pulmonary_alveolus"),
    ("Breathing rate is determined mainly by blood CO2 level; central chemoreceptors in the medulla; oxygen is secondary", "https://en.wikipedia.org/wiki/Control_of_ventilation"),
    ("Shallow-water blackout follows voluntary hyperventilation before a breath-hold dive (low CO2 expedites the lack of oxygen); with CO2 as the main driver of the urge (see Control of ventilation) low CO2 means a weaker urge", "https://en.wikipedia.org/wiki/Shallow_water_blackout"),
    ("The epiglottis folds over the airway during swallowing so food enters the esophagus", "https://en.wikipedia.org/wiki/Epiglottis"),
    ("Cells use glucose and oxygen to make CO2, water and ATP in the mitochondria; this releases heat", "https://www.khanacademy.org/science/ap-biology/cellular-energetics/cellular-respiration-ap/a/intro-to-cellular-respiration"),
    ("Oxidative phosphorylation in eukaryotes takes place in mitochondria and makes most of the ATP", "https://openstax.org/books/biology-2e/pages/7-1-energy-in-living-systems"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
