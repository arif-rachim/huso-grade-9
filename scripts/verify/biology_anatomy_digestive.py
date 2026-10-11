"""Independent checks for materi/biology/anatomy-digestive.md (logic items + fact-check list)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/anatomy-digestive.md").read_text()
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


# ---- model: facts as data --------------------------------------------------------------------
CANAL = ["mouth", "esophagus", "stomach", "small intestine", "large intestine", "rectum", "anus"]
GLANDS_NOT_ON_PATH = {"liver", "gallbladder", "pancreas"}
KCAL_PER_G = {"carbohydrate": 4, "protein": 4, "fat": 9}
GLAND = {  # gland -> (juice, key content, has enzymes?)
    "salivary glands": ("saliva", "amylase", True),
    "gastric glands": ("gastric juice", "HCl + pepsin", True),
    "liver": ("bile", "bile salts", False),
    "pancreas": ("pancreatic juice", "enzymes", True),
    "intestinal glands": ("intestinal juice", "enzymes", True),
}
FIRST_SITE = {"starch": "mouth", "protein": "stomach"}      # where digestion begins
DEFICIENCY = {
    "vitamin A": "night blindness", "vitamin B1": "beriberi", "vitamin C": "scurvy", "vitamin D": "rickets",
    "iron": "anemia", "iodine": "goiter", "protein": "kwashiorkor", "all food (energy)": "marasmus",
}

# text: canal order line + the figure
ok("**mouth → esophagus → stomach → small intestine → large intestine → rectum → anus.**" in TXT)
ok(" → ".join(CANAL) in TXT)
ok("not** part of the food tube" in TXT and GLANDS_NOT_ON_PATH.isdisjoint(CANAL))
svg = (ROOT / "public/content/biology/digestive-canal.svg").read_text()
labs = re.findall(r'data-label="([^"]+)"', svg)
ok(set(CANAL) | GLANDS_NOT_ON_PATH <= set(labs), labs)
# vertical order in the picture follows the canal order (y of the label text)
ys = {w: int(re.search(rf'<text x="356" y="(\d+)">{w.capitalize()}</text>', svg).group(1)) for w in ["mouth", "esophagus", "stomach", "small intestine", "rectum", "anus"]}
ok(ys["mouth"] < ys["esophagus"] < ys["stomach"] < ys["small intestine"] < ys["rectum"] < ys["anus"], ys)

# glands: figure table compared with the model
gsvg = (ROOT / "public/content/biology/digestive-glands.svg").read_text()
for g, (juice, content, enz) in GLAND.items():
    ok(f'data-label="{g}"' in gsvg, g)
ok("has NO enzymes" in gsvg and "bile" in gsvg.lower())
ok([g for g, v in GLAND.items() if not v[2]] == ["liver"])
ok("**bile**, which has **no enzymes**" in TXT)
gl_order = [m for m in re.findall(r'data-label="([^"]+)"', gsvg)]
ok(gl_order == list(GLAND), gl_order)   # same order as food meets them

# ---- deficiency table: text, figure and model agree --------------------------------------
core6 = TXT.split("6. **Deficiency diseases**")[1].split("![")[0]
pairs = re.findall(r"\*\*([^*]+)\*\* → \*\*([^*]+)\*\*", core6)
txt_pairs = {a: b for a, b in pairs}
for k, v in DEFICIENCY.items():
    if k.startswith("all food"):
        ok("too little food overall → **marasmus**" in core6)
        continue
    ok(txt_pairs.get(k) == v, (k, txt_pairs.get(k), v))
dsvg = (ROOT / "public/content/biology/digestive-deficiency.svg").read_text()
for k, v in DEFICIENCY.items():
    ok(f'data-label="{k.lower()} - {v}"' in dsvg, (k, v))
ok(len(set(DEFICIENCY.values())) == len(DEFICIENCY))
# classes of food: exactly 7
fsvg = (ROOT / "public/content/biology/digestive-food-classes.svg").read_text()
classes = ["Carbohydrates", "Proteins", "Fats", "Vitamins", "Minerals", "Water", "Roughage (fiber)"]
ok(all(c in fsvg for c in classes) and len(classes) == 7 and "Seven classes" in fsvg)
ok("(7)" in TXT and "carbohydrate **4 kcal**, protein **4 kcal**, fat **9 kcal**" in TXT)

# ---- Example 1: energy ----------------------------------------------------------------------------
grams = {"carbohydrate": 30, "protein": 10, "fat": 8}
energy = sum(grams[k] * KCAL_PER_G[k] for k in grams)
ok(energy == 232)
o = options("**Example 1.**")
val = {k: int(re.match(r"\d+", v).group(0)) for k, v in o.items()}
ok([k for k, v in val.items() if v == energy] == ["D"])
ok(val["A"] == sum(grams.values()) == 48)                                   # total grams
ok(val["B"] == grams["carbohydrate"] * 4 + grams["protein"] * 4 == 160)    # no fat
ok(val["C"] == sum(grams.values()) * 4 == 192)                              # fat at 4
ok(val["E"] == sum(grams.values()) * 9 == 432)                              # all at 9
ok(re.search(r"\*\*Answer: \(D\)\.\*\*", TXT) is not None)

# ---- Example 2: where digestion begins --------------------------------------------------------------
o = options("**Example 2.**")
want = f"{FIRST_SITE['starch']}, {FIRST_SITE['protein']}"
ok([k for k, v in o.items() if v == want] == ["A"], want)
ok(CANAL.index(FIRST_SITE["starch"]) < CANAL.index(FIRST_SITE["protein"]))   # mouth comes before stomach
ok(re.search(r"\*\*Answer: \(A\)\.\*\*", TXT) is not None)

# ---- Q1: order of organs ------------------------------------------------------------------------------
o = options("**1.**")
seqs = {k: [s.strip() for s in v.split("→")] for k, v in o.items()}
true_prefix = CANAL[:6]
hits = [k for k, s in seqs.items() if s == true_prefix]
ok(hits == ["C"] and key_letter(1) == "C", hits)
ok(all(sorted(seqs[k]) == sorted(true_prefix) for k in "ABD"))       # same organs, wrong order
ok("liver" in seqs["E"] and "liver" not in CANAL)

# ---- Q2: bile ------------------------------------------------------------------------------------------------
o = options("**2.**")
correct = [k for k, v in o.items() if v.startswith("liver;") and "tiny droplets" in v]
ok(correct == ["D"] and key_letter(2) == "D")
ok(not GLAND["liver"][2] and "lipase" in o["C"])        # bile has no enzymes -> C is false

# ---- Q3: iron/anemia ------------------------------------------------------------------------------------------
o = options("**3.**")
ok(o["A"] == "iron" and DEFICIENCY["iron"] == "anemia" and key_letter(3) == "A")
ok(DEFICIENCY["iodine"] == "goiter" and DEFICIENCY["vitamin D"] == "rickets" and DEFICIENCY["vitamin A"] == "night blindness")

# ---- Q4: butter vs sugar --------------------------------------------------------------------------------------------
butter, sugar = 10 * KCAL_PER_G["fat"], 20 * KCAL_PER_G["carbohydrate"]
ok((butter, sugar, butter - sugar) == (90, 80, 10))
o = options("**4.**")
val = {k: int(re.match(r"\d+", v).group(0)) for k, v in o.items()}
ok([k for k, v in val.items() if v == butter - sugar] == ["B"] and key_letter(4) == "B")
ok(val["C"] == butter - 10 * 4 and val["D"] == sugar and val["E"] == butter + sugar and val["A"] == 0)

# ---- Q5: absorption -----------------------------------------------------------------------------------------------------
o = options("**5.**")
ok([k for k, v in o.items() if v.startswith("the small intestine") and "villi" in v] == ["E"] and key_letter(5) == "E")

letters = [key_letter(q) for q in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in "ABCDE") and len(letters) == 5, letters)
ok(len(re.findall(r"^\d\. \*\*\(", KEYBLOCK, re.M)) == 5)
ok("🍳" in TXT.split("## ✅ Check")[1] and "🏊" in TXT.split("## ✅ Check")[1])

FACT_CHECKS = [
    ("Salivary amylase starts starch digestion in the mouth; carbohydrate digestion continues in the small intestine", "https://openstax.org/books/biology-2e/pages/34-3-digestive-system-processes"),
    ("Stomach: parietal cells make HCl, pepsinogen becomes pepsin which digests proteins", "https://openstax.org/books/biology-2e/pages/34-1-digestive-systems"),
    ("Liver makes bile, stored in the gallbladder; bile salts emulsify fats", "https://openstax.org/books/biology-2e/pages/34-1-digestive-systems"),
    ("Bile contains no digestive enzymes; it emulsifies fat so pancreatic lipase can act", "https://en.wikipedia.org/wiki/Bile"),
    ("Pancreatic juice has bicarbonate and enzymes for proteins, carbohydrates and fats", "https://openstax.org/books/biology-2e/pages/34-1-digestive-systems"),
    ("Small intestine is longer than the large one, called small because it is narrower; villi increase absorption surface", "https://en.wikipedia.org/wiki/Small_intestine"),
    ("Large intestine reabsorbs water; rectum stores feces; esophagus moves food by peristalsis", "https://openstax.org/books/biology-2e/pages/34-1-digestive-systems"),
    ("Energy per gram: fat 9 kcal, protein 4 kcal, carbohydrate 4 kcal", "https://en.wikipedia.org/wiki/Food_energy"),
    ("Humans cannot digest cellulose; fiber helps move waste through the large intestine", "https://openstax.org/books/biology-2e/pages/34-2-nutrition-and-energy-production"),
    ("Scurvy (vitamin C), rickets (vitamin D), night blindness (vitamin A), anemia (iron), goiter (iodine), beriberi (thiamine, B1)", "https://openstax.org/books/biology-2e/pages/34-2-nutrition-and-energy-production"),
    ("Scurvy is caused by vitamin C deficiency", "https://en.wikipedia.org/wiki/Vitamin_C"),
    ("Rickets: most commonly vitamin D deficiency, soft weak bones", "https://en.wikipedia.org/wiki/Rickets"),
    ("Goitre: over 90 % of cases caused by iodine deficiency", "https://en.wikipedia.org/wiki/Goitre"),
    ("Night blindness: vitamin A deficiency (rhodopsin is made from vitamin A)", "https://en.wikipedia.org/wiki/Night_blindness"),
    ("Iron is a component of hemoglobin; iron lack causes anemia", "https://en.wikipedia.org/wiki/Iron-deficiency_anemia"),
    ("Kwashiorkor = protein deficiency with edema; marasmus = overall energy deficiency", "https://en.wikipedia.org/wiki/Kwashiorkor"),
    ("Malnutrition = deficiencies, excesses or imbalances in intake of energy and/or nutrients", "https://www.who.int/news-room/fact-sheets/detail/malnutrition"),
    ("Dietary fiber cannot be broken down by human digestive enzymes", "https://en.wikipedia.org/wiki/Dietary_fiber"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
