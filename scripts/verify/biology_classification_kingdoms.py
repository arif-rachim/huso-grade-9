"""Independent checks for materi/biology/classification-kingdoms.md.

Kingdom features are a lookup table: organisms are classified from their features (nucleus,
cell wall, number of cells, food), the markdown table and the SVG table are compared with it,
and the numeric/logical items (counting fungi, doubling, five vertebrate classes) are recomputed."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/classification-kingdoms.md").read_text()
SVG = (ROOT / "public/content/biology/kingdoms-five.svg").read_text()
n = 0


def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1


def options(label):
    i = TXT.index(label)
    block = TXT[i:].split("\n\n")[1]
    return dict(re.findall(r"\(([A-E])\) (.*?)(?=\s+\([A-E]\) |\n|$)", block.replace("\n", "  \n")))


def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", TXT.split("<details>")[1], re.M).group(1)


# kingdom features: (nucleus, wall, cells, food)
K = {
    "Monera": dict(nucleus=False, wall="yes", cells="one", food="varies", example="bacteria"),
    "Protista": dict(nucleus=True, wall="some", cells="one", food="varies", example="Amoeba"),
    "Fungi": dict(nucleus=True, wall="chitin", cells="threads", food="absorbs", example="bread mould"),
    "Plantae": dict(nucleus=True, wall="cellulose", cells="many", food="photosynthesis", example="mango tree"),
    "Animalia": dict(nucleus=True, wall="none", cells="many", food="eats", example="fish, human"),
}
ok(list(K) == ["Monera", "Protista", "Fungi", "Plantae", "Animalia"])
ok(sum(1 for v in K.values() if not v["nucleus"]) == 1)  # only Monera lacks a nucleus

# markdown table equals the lookup
rows = re.findall(r"^\| \*\*(\w+)\*\* \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|$", TXT, re.M)
ok([r[0] for r in rows] == list(K))
for name, ctype, body, food, ex in rows:
    ok((ctype == "prokaryote") == (not K[name]["nucleus"]))
    ok(K[name]["example"] == ex)
    kf = K[name]["food"]
    ok(kf in food or (kf == "eats" and "eats" in food) or kf == "varies" and food == "varies")
    ok({"one": "one cell", "threads": "threads (hyphae)", "many": "many cells"}[K[name]["cells"]] == body)
# SVG table says the same things
text = " ".join(re.findall(r">([^<]+)</text>", SVG))
for word in ("prokaryote", "chitin", "cellulose", "none", "Amoeba", "bread mould", "mango tree", "fish, human", "bacteria"):
    ok(word in text, word)
ok(text.count("eukaryote") == 4)


def classify(nucleus, wall, cells, food):
    if not nucleus:
        return "Monera"
    if cells == "one":
        return "Protista" if wall != "chitin" else "Fungi"
    if wall == "none" and food == "eats":
        return "Animalia"
    if wall == "chitin" and food == "absorbs":
        return "Fungi"
    if wall == "cellulose":
        return "Plantae"
    return "?"


# ---- Example 1: count of fungi in the kitchen
kitchen = {"mould": ("Fungi",), "mushroom": ("Fungi",), "yeast": ("Fungi",), "yogurt bacteria": ("Monera",), "rice": ("Plantae",)}
nfungi = sum(1 for v in kitchen.values() if v[0] == "Fungi")
ok(nfungi == 3)
# yeast: one cell, nucleus, chitin wall -> fungus by the chitin rule; bacteria: no nucleus
ok(classify(True, "chitin", "one", "absorbs") == "Fungi")
ok(classify(False, "yes", "one", "varies") == "Monera")
o = options("**Example 1.**")
ok({k: int(v) for k, v in o.items()} == {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5})
hits = [k for k, v in o.items() if int(v) == nfungi]
ok(hits == ["C"], hits)
ok(nfungi - 1 == 2 and nfungi + 1 == 4)  # (B) forgets the yeast, (D) adds the bacteria
ok("**Answer: (C).**" in TXT.split("**Example 2.**")[0])
ok("(1) green mould" in TXT and "(5) a rice plant" in TXT)

# ---- Example 2: Amoeba
AMOEBA = dict(nucleus=True, locomotion="pseudopodia", food="engulfs", vacuoles={"food", "contractile"}, repro={"binary fission", "multiple fission"}, resp="diffusion")
o = options("**Example 2.**")
ok(len(o) == 5)
good = []
for k, v in o.items():
    vl = v.lower()
    if "pseudopodia" in vl and "food vacuole" in vl and "contractile vacuole" in vl:
        good.append(k)
ok(good == ["B"], good)
ok("flagella" in o["A"] and "photosynthesis" in o["A"] and AMOEBA["locomotion"] != "flagella")
ok("no nucleus" in o["C"] and AMOEBA["nucleus"])
ok("spores" in o["D"] and "spores" not in AMOEBA["repro"])
ok("gills" in o["E"] and AMOEBA["resp"] == "diffusion")
ok("**Answer: (B).**" in TXT.split("**Example 2.**")[1].split("## ⚠️")[0])

# ---- Q1: bacteria
o = options("**1.** Which description")
def bacteria_ok(v):
    v = v.lower()
    return "no nucleus" in v and "round" in v and "rod" in v and "spiral" in v
hits = [k for k, v in o.items() if bacteria_ok(v)]
ok(hits == ["A"] and key_letter(1) == "A")
ok("cellulose" in o["B"] and "hyphae" in o["C"] and "pseudopodia" in o["D"] and "chloroplasts" in o["E"])

# ---- Q2: mould
o = options("**2.** 🍳")
hits = [k for k, v in o.items() if v.startswith("It is a fungus") and "absorb" in v and "hyphae" in v]
ok(hits == ["D"] and key_letter(2) == "D")
ok("photosynthesis" in o["E"] and K["Fungi"]["food"] != "photosynthesis")

# ---- Q3: doubling
pop = 1
for hour in range(5):
    pop *= 2
ok(pop == 32 and 2 ** 5 == 32)
o = options("**3.** Suppose")
hits = [k for k, v in o.items() if int(v) == pop]
ok(hits == ["B"] and key_letter(3) == "B")
ok(2 ** 4 == int(o["C"]) and 2 ** 6 == int(o["E"]) and 1 + 5 == 6 and int(o["A"]) == 5 and int(o["D"]) == 2 * 5)

# ---- Q4: five classes
CLASS = {"shark": "fish", "tuna": "fish", "trout": "fish", "salmon": "fish", "eel": "fish",
         "frog": "amphibian", "toad": "amphibian", "newt": "amphibian", "salamander": "amphibian",
         "lizard": "reptile", "crocodile": "reptile", "snake": "reptile", "turtle": "reptile", "tortoise": "reptile",
         "eagle": "bird", "penguin": "bird", "sparrow": "bird", "ostrich": "bird",
         "bat": "mammal", "dolphin": "mammal", "lion": "mammal", "octopus": "invertebrate", "spider": "invertebrate"}
ok({c for c in CLASS.values() if c != "invertebrate"} == {"fish", "amphibian", "reptile", "bird", "mammal"})
o = options("**4.** Which list")
hits = []
for k, v in o.items():
    animals = [a.strip().lower() for a in v.split(",")]
    classes = {CLASS[a] for a in animals}
    if classes == {"fish", "amphibian", "reptile", "bird", "mammal"} and len(animals) == 5:
        hits.append(k)
ok(hits == ["C"] and key_letter(4) == "C", hits)
ok("invertebrate" in {CLASS[a.strip().lower()] for a in o["B"].split(",")})
ok("invertebrate" in {CLASS[a.strip().lower()] for a in o["D"].split(",")})
ok("mammal" not in {CLASS[a.strip().lower()] for a in o["E"].split(",")})
ok("bird" not in {CLASS[a.strip().lower()] for a in o["A"].split(",")})

# ---- Q5: classify X and Y
X = classify(False, "yes", "one", "varies")
Y = classify(True, "none", "many", "eats")
ok((X, Y) == ("Monera", "Animalia"))
o = options("**5.** Organism X")
hits = [k for k, v in o.items() if tuple(s.strip() for s in v.split(",")) == (X, Y)]
ok(hits == ["E"] and key_letter(5) == "E")

keys = [key_letter(i) for i in range(1, 6)]
ok(len(keys) == 5 and all(keys.count(c) <= 2 for c in "ABCDE"), keys)
for i in range(1, 6):
    blk = re.search(rf"^\*\*{i}\.\*\*(.*?)(?=^\*\*{i+1}\.\*\*|<details>)", TXT, re.S | re.M).group(1)
    ok(len(re.findall(r"\(([A-E])\)", blk)) == 5)

FACT_CHECKS = [
    ("Whittaker's 1969 five kingdoms: Monera, Protista, Fungi, Plantae, Animalia, based mainly on nutrition", "https://en.wikipedia.org/wiki/Kingdom_(biology)"),
    ("Bacteria are prokaryotes without a nucleus and rarely have membrane-bound organelles; they have ribosomes", "https://en.wikipedia.org/wiki/Bacteria"),
    ("Bacteria shapes: cocci (spherical), bacilli (rod), spiral forms (spirilla)", "https://en.wikipedia.org/wiki/Bacteria"),
    ("Bacterial flagella are used for movement", "https://en.wikipedia.org/wiki/Bacteria"),
    ("Almost all prokaryotes have a cell wall", "https://openstax.org/books/biology-2e/pages/22-1-prokaryotic-diversity"),
    ("Amoebae lack cell walls and move by pseudopods; they feed by phagocytosis (engulfing)", "https://en.wikipedia.org/wiki/Amoeba"),
    ("Freshwater amoebae use a contractile vacuole to expel excess water", "https://en.wikipedia.org/wiki/Amoeba"),
    ("Amoeba: food vacuole digestion, diffusion of gases, binary and multiple fission (encystment)", "https://www.careers360.com/biology/amoeba-diagram-topic-pge"),
    ("Fungi are built of hyphae forming a mycelium, have chitin cell walls, and absorb food after exoenzymes digest it outside", "https://openstax.org/books/biology-2e/pages/24-1-characteristics-of-fungi"),
    ("Most fungi are saprobes and obligate aerobes; yeasts can ferment without oxygen", "https://openstax.org/books/biology-2e/pages/24-1-characteristics-of-fungi"),
    ("Rhizopus (black bread mould) is a saprotroph with stolons, rhizoids and sporangia", "https://en.wikipedia.org/wiki/Rhizopus_stolonifer"),
    ("Vertebrate classes: fish, amphibians, reptiles, birds, mammals; less than 5% of animal species are vertebrates", "https://en.wikipedia.org/wiki/Vertebrate"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
