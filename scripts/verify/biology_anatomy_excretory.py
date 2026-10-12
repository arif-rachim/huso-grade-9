"""Independent checks for materi/biology/anatomy-excretory.md (logic items + fact-check list)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/anatomy-excretory.md").read_text()
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


# ---- model: the facts as data --------------------------------------------------------
URINE_PATH = ["kidney", "ureter", "bladder", "urethra"]
PRODUCTS = {  # organ -> (what it removes)
    "kidneys": {"urea", "water", "salts"},
    "sweat glands": {"water", "salts", "urea"},
    "lungs": {"carbon dioxide", "water vapor"},
}
MADE_BY_CELLS = {"carbon dioxide", "urea", "water", "salts", "water vapor"}
NOT_MADE_BY_CELLS = {"undigested fiber"}          # never absorbed -> egestion
COUNT = {"kidney": 2, "ureter": 2, "bladder": 1, "urethra": 1}

# text states the same path, in order
ok("kidney → ureter → bladder → urethra" in TXT)
ok(["kidney", "ureter", "bladder", "urethra"] == URINE_PATH)
core3 = TXT.split("3. **The urinary system.**")[1].split("4. **Kidneys filter blood.**")[0]
ok(core3.index("kidneys") < core3.index("ureter") < core3.index("bladder") < core3.index("urethra"))
ok(COUNT["ureter"] == 2 and COUNT["urethra"] == 1 and "there are **two**" in TXT and "only **one**" in TXT)

# the figure with the three routes names exactly these products
svg = (ROOT / "public/content/biology/excretory-routes.svg").read_text()
for w in ["carbon dioxide", "water vapor", "water, salts", "urea", "urine", "sweat"]:
    ok(w in svg, w)
svg2 = (ROOT / "public/content/biology/excretory-urinary-system.svg").read_text()
for lab in ["kidney", "ureter", "urinary bladder", "urethra"]:
    ok(f'data-label="{lab}"' in svg2, lab)
ok("1 million nephrons" in (ROOT / "public/content/biology/excretory-kidney-filter.svg").read_text())

# nephrons: about 1 million in each kidney -> about 2 million (the syllabus says "millions")
NEPHRONS_PER_KIDNEY = 1_000_000
ok(NEPHRONS_PER_KIDNEY * COUNT["kidney"] == 2_000_000 and "about 2 million" in TXT)

# ---- Example 1: dehydrated swimmer -> less, more concentrated urine -----------------------
def urine(water_in, water_lost_elsewhere, solute_to_remove=1.0):
    vol = max(water_in - water_lost_elsewhere, 0.2)          # kidneys keep a minimum volume
    return vol, solute_to_remove / vol                         # (volume, concentration)
v_normal, c_normal = urine(2.0, 0.9)
v_hot, c_hot = urine(0.8, 0.9 + 0.8)                           # drinks little, sweats +0.8 L
ok(v_hot < v_normal and c_hot > c_normal)                      # small, concentrated
ok(c_hot > 0)                                                  # urea still removed (not "no urea")
o = options("**Example 1.**")
ok([k for k, v in o.items() if v.startswith("a small amount of dark")] == ["B"])
ok(re.search(r"\*\*Answer: \(B\)\.\*\*", TXT) is not None)

# ---- Example 2: not excretion = undigested fiber ------------------------------------------
o = options("**Example 2.**")
cases = {"A": "carbon dioxide", "B": "water", "C": "urea", "D": "undigested fiber", "E": "water vapor"}
not_exc = [k for k, prod in cases.items() if prod not in MADE_BY_CELLS]
ok(not_exc == ["D"], not_exc)
ok(o["D"].startswith("passing undigested fiber"))
ok(re.search(r"\*\*Answer: \(D\)\.\*\*", TXT) is not None)

# ---- Q1: path of urine -----------------------------------------------------------------------
o = options("**1.**")
seqs = {k: [s.strip() for s in v.split("→")] for k, v in o.items()}
ok([k for k, s in seqs.items() if s == URINE_PATH] == ["D"] and key_letter(1) == "D")
ok(sorted(seqs["C"]) == sorted(URINE_PATH) and seqs["C"] != URINE_PATH)    # same organs, wrong order

# ---- Q2: CO2 leaves via lungs ----------------------------------------------------------------
route_of = {org: p for org, p in PRODUCTS.items() if "carbon dioxide" in p}
ok(list(route_of) == ["lungs"])
o = options("**2.**")
ok(o["A"].startswith("the lungs") and key_letter(2) == "A")
ok("carbon dioxide" not in PRODUCTS["kidneys"] and "carbon dioxide" not in PRODUCTS["sweat glands"])

# ---- Q3: nitrogen-containing waste = urea ---------------------------------------------------------
FORMULA = {"glucose": "C6H12O6", "bile": None, "carbon dioxide": "CO2", "fatty acids": "CxHyO2", "urea": "CH4N2O"}
has_N = [name for name, f in FORMULA.items() if f and "N" in f]
ok(has_N == ["urea"], has_N)
o = options("**3.**")
ok(o["E"] == "urea" and key_letter(3) == "E")

# ---- Q4: water balance, in milliliters to avoid float error --------------------------------------
drink, sweat_breath, feces = 2000, 900, 100
urine_ml = drink - sweat_breath - feces
ok(urine_ml == 1000)
o = options("**4.**")
val = {k: int(round(float(re.match(r"[\d.]+", v).group(0)) * 1000)) for k, v in o.items()}
ok([k for k, v in val.items() if v == urine_ml] == ["B"] and key_letter(4) == "B")
ok(val["A"] == sweat_breath and val["C"] == drink - sweat_breath and val["D"] == drink - feces and val["E"] == drink + sweat_breath + feces)

# ---- Q5: kidney facts -----------------------------------------------------------------------------------
STATEMENTS = {
    "A": False,  # urea is made in the liver
    "B": False,  # the bladder stores urine
    "C": True,   # about a million nephrons per kidney
    "D": False,  # feces come from the large intestine
    "E": False,  # kidneys are behind the abdomen, not in the chest
}
ok([k for k, v in STATEMENTS.items() if v] == ["C"])
o = options("**5.**")
ok("million nephrons" in o["C"] and key_letter(5) == "C")

# ---- letters, themes -------------------------------------------------------------------------------------
letters = [key_letter(q) for q in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in "ABCDE") and len(letters) == 5, letters)
ok(len(re.findall(r"^\d\. \*\*\(", KEYBLOCK, re.M)) == 5)
ok("🍳" in TXT.split("## ✅ Check")[1] or "🏊" in TXT.split("## ✅ Check")[1])

# ---- FACT CHECKS -------------------------------------------------------------------------------------------
FACT_CHECKS = [
    ("The excretory system removes waste via skin (sweat), lungs (CO2) and the urinary system (urine)", "https://openstax.org/books/concepts-biology/pages/16-1-homeostasis-and-osmoregulation"),
    ("Each kidney has more than a million nephrons that filter the blood; ureters, bladder, urethra roles", "https://openstax.org/books/concepts-biology/pages/16-1-homeostasis-and-osmoregulation"),
    ("Kidneys: functional unit nephron (~1 million per kidney); sweat glands lose water and electrolytes; lungs lose water vapor", "https://openstax.org/books/biology-2e/pages/41-2-the-kidneys-and-osmoregulatory-organs"),
    ("Kidneys lie on either side of the spine (T12-L3), about 1 million nephrons each, right kidney slightly lower", "https://en.wikipedia.org/wiki/Kidney"),
    ("Ureters carry urine to the bladder by peristalsis; bladder stores it; urethra carries it outside", "https://openstax.org/books/anatomy-and-physiology-2e/pages/25-2-gross-anatomy-of-urine-transport"),
    ("Urea forms in the liver from amino acid breakdown, is filtered by the kidneys; a little leaves in sweat", "https://en.wikipedia.org/wiki/Urea"),
    ("Urine is about 91-96 % water, urea is its largest solid; adult output about 1.4 L per day", "https://en.wikipedia.org/wiki/Urine"),
    ("Sweat is mostly water with minerals and traces of urea; sweating is mainly thermoregulation", "https://en.wikipedia.org/wiki/Perspiration"),
    ("Water loss raises ADH so kidneys keep water: lower volume, more concentrated urine", "https://openstax.org/books/anatomy-and-physiology-2e/pages/26-2-water-balance"),
    ("Nephrons filter, reabsorb and secrete; useful substances return to the blood", "https://openstax.org/books/biology-2e/pages/41-2-the-kidneys-and-osmoregulatory-organs"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
