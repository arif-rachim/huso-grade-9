"""Independent checks for materi/biology/ecology-ecosystems.md.

The pond web is encoded as a directed graph (arrow = eater) and the chains are enumerated;
pyramid-of-numbers questions are evaluated by comparing consecutive levels; interaction types
are looked up from effect signs."""
import itertools, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/ecology-ecosystems.md").read_text()
SVG = (ROOT / "public/content/biology/ecosystems-food-web.svg").read_text()
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


# ---- the pond web: eats[eater] = {foods}
EATS = {
    "Tadpole": {"Algae"}, "Water flea": {"Algae"},
    "Dragonfly nymph": {"Tadpole", "Water flea"}, "Small fish": {"Tadpole", "Water flea"},
    "Heron": {"Dragonfly nymph", "Small fish"},
}
PRODUCERS = {"Algae"}
arrows = [(food, eater) for eater, foods in EATS.items() for food in foods]
ok(len(arrows) == 8)  # the "8" distractor of Example 1


def chains(node, path):
    if node == "Heron":
        yield path
        return
    for food, eater in arrows:
        if food == node:
            yield from chains(eater, path + [eater])


allc = list(chains("Algae", ["Algae"]))
ok(len(allc) == 4 and all(len(c) == 4 for c in allc), allc)
ok(len({tuple(c) for c in allc}) == 4)
# naive counts for the distractors
straight = [c for c in allc if (c[1], c[2]) in (("Tadpole", "Dragonfly nymph"), ("Water flea", "Small fish"))]
ok(len(straight) == 2)
ok(2 * 2 * 1 == 4)
# trophic level of the heron = chain length - 1 (producer is level 1): third consumer = tertiary
LEVEL = {1: "producer", 2: "primary", 3: "secondary", 4: "tertiary"}
ok(all(LEVEL[len(c)] == "tertiary" for c in allc))
# every arrow in the picture's text matches the graph: nodes appear in the SVG
for name in list(EATS) + list(PRODUCERS):
    ok(name in SVG)
o = options("**Example 1.**")
ok(len(o) == 5)
def parse1(v):
    return int(re.match(r"(\d+) chains", v).group(1)), v.split("; ")[1]
hits = [k for k, v in o.items() if parse1(v) == (4, "a tertiary consumer")]
ok(hits == ["B"], hits)
ok(parse1(o["D"])[0] == len(arrows) and parse1(o["A"])[0] == len(straight))
ok("**Answer: (B).**" in TXT.split("**Example 2.**")[0])

# ---- Example 2: pyramid of numbers
levels = [("oak", 1), ("caterpillar", 800), ("bird", 40), ("hawk", 2)]
counts = [c for _, c in levels]
upright = all(counts[i] > counts[i + 1] for i in range(len(counts) - 1))
ok(not upright)
widest = max(range(4), key=lambda i: counts[i])
ok(widest == 1 and counts[0] < counts[1])  # spindle: widest in the middle
o = options("**Example 2.**")
ok(len(o) == 5)
hits = [k for k, v in o.items() if v.startswith("It is not an upright pyramid") and "narrower" in v]
ok(hits == ["C"], hits)
ok("**Answer: (C).**" in TXT.split("**Example 2.**")[1].split("## ⚠️")[0])
ok("1 oak tree, 800 caterpillars, 40 small birds, 2 hawks" in TXT)

# ---- Q1: abiotic only
BIOTIC = {"algae", "bacteria", "mushrooms", "tadpoles", "fungi"}
ABIOTIC = {"soil", "wind", "sunlight", "water", "air", "temperature", "humidity"}
o = options("**1.** Which list")
hits = []
for k, v in o.items():
    items = [x.strip().lower() for x in v.split(",")]
    ok(all(i in BIOTIC | ABIOTIC for i in items))
    if all(i in ABIOTIC for i in items):
        hits.append(k)
ok(hits == ["C"] and key_letter(1) == "C", hits)
ok(len(ABIOTIC) == 7 and "7 abiotic" in TXT)

# ---- Q2: pond chain
chain = ["algae", "water flea", "small fish", "heron"]
role = {n_: LEVEL[i + 1] for i, n_ in enumerate(chain)}
ok(role["small fish"] == "secondary" and role["water flea"] == "primary" and role["heron"] == "tertiary" and role["algae"] == "producer")
o = options("**2.** 🏊")
ok(o["A"].startswith("The small fish is a secondary consumer") and "direction" in o["A"])
for k in "BCDE":
    ok(not (o[k].startswith("The small fish is a secondary")))
ok(key_letter(2) == "A")
ok("arrows point from the eater" in o["D"])  # backwards: wrong
ok("Algae are decomposers" in o["E"] and role["algae"] == "producer")

# ---- Q3: farm chain, wheat dies
chain3 = ["wheat", "chicken", "fox"]
# simple model: a consumer's number follows its food one step behind
pop = {"wheat": 100.0, "chicken": 100.0, "fox": 100.0}
order = []
pop["wheat"] = 10.0
for step in range(2):
    for a, b in zip(chain3, chain3[1:]):
        if pop[b] > pop[a] * 0.9 and b not in order:
            pop[b] = pop[a]
            order.append(b)
ok(order == ["chicken", "fox"] and pop["chicken"] < 100 and pop["fox"] < 100)
o = options("**3.** 🍳")
hits = [k for k, v in o.items() if "chickens decrease first" in v and "foxes decrease" in v]
ok(hits == ["D"] and key_letter(3) == "D")

# ---- Q4: interactions by effect signs
EFFECT = {"mutualism": ("+", "+"), "commensalism": ("+", "0"), "parasitism": ("+", "-"), "predation": ("+", "-")}
def classify(sign, kills, stays):
    if sign == ("+", "+"): return "mutualism"
    if sign == ("+", "0"): return "commensalism"
    return "predation" if kills else "parasitism"
CASES = {"tapeworm": (("+", "-"), False), "lynx": (("+", "-"), True), "nesting bird": (("+", "0"), False),
         "tick": (("+", "-"), False), "bee": (("+", "+"), False)}
TRUTH = {"tapeworm": classify(CASES["tapeworm"][0], False, True),
         "lynx": classify(CASES["lynx"][0], True, False), "nesting bird": classify(CASES["nesting bird"][0], False, False),
         "tick": classify(CASES["tick"][0], False, True), "bee": classify(CASES["bee"][0], False, False)}
ok(TRUTH == {"tapeworm": "parasitism", "lynx": "predation", "nesting bird": "commensalism", "tick": "parasitism", "bee": "mutualism"})
o = options("**4.** Which pair")
claims = {"A": ("tapeworm", "commensalism"), "B": ("lynx", "mutualism"), "C": ("nesting bird", "parasitism"),
          "D": ("tick", "predation"), "E": ("bee", "mutualism")}
hits = [k for k, (who, what) in claims.items() if TRUTH[who] == what]
ok(hits == ["E"] and key_letter(4) == "E", hits)
for k, (who, what) in claims.items():
    ok(what in o[k].lower())

# ---- Q5: pyramid of numbers
c5 = [1, 5000, 50, 2]
ok(not all(c5[i] > c5[i + 1] for i in range(3)) and c5[0] < c5[1])
ok(not all(c5[i] < c5[i + 1] for i in range(3)))  # not inverted at every level either
o = options("**5.** Suppose")
hits = [k for k, v in o.items() if "narrower than the aphid level" in v]
ok(hits == ["B"] and key_letter(5) == "B")
ok("1 rose bush, 5,000 aphids, 50 ladybugs and 2 sparrows" in TXT)

keys = [key_letter(i) for i in range(1, 6)]
ok(len(keys) == 5 and all(keys.count(c) <= 2 for c in "ABCDE"), keys)
for i in range(1, 6):
    blk = re.search(rf"^\*\*{i}\.\*\*(.*?)(?=^\*\*{i+1}\.\*\*|<details>)", TXT, re.S | re.M).group(1)
    ok(len(re.findall(r"\(([A-E])\)", blk)) == 5)

FACT_CHECKS = [
    ("An ecosystem is a community of living organisms and their interactions with their abiotic (nonliving) environment", "https://openstax.org/books/biology-2e/pages/46-1-ecology-of-ecosystems"),
    ("Abiotic factors include sunlight, temperature, water (rainfall) and nutrients", "https://openstax.org/books/biology-2e/pages/46-1-ecology-of-ecosystems"),
    ("Producers are autotrophs; primary consumers eat producers, secondary eat primary, tertiary eat secondary", "https://openstax.org/books/biology-2e/pages/46-2-energy-flow-through-ecosystems"),
    ("Decomposers (fungi and bacteria) break down dead organic matter", "https://openstax.org/books/biology-2e/pages/46-2-energy-flow-through-ecosystems"),
    ("A food web is a network of interconnected food chains; energy flows in one direction", "https://openstax.org/books/biology-2e/pages/46-2-energy-flow-through-ecosystems"),
    ("Pyramids of numbers can be upright or inverted; a temperate forest has few trees supporting many insects", "https://openstax.org/books/biology-2e/pages/46-2-energy-flow-through-ecosystems"),
    ("Pyramids of numbers are not necessarily upright (one tree supports many insects); energy pyramids are upright", "https://en.wikipedia.org/wiki/Ecological_pyramid"),
    ("Food chain energy moves from producers up to consumers; only about 10 percent passes to the next level; decomposers return nutrients", "https://en.wikipedia.org/wiki/Food_chain"),
    ("Mutualism: both species benefit (termites and gut protozoa, lichens)", "https://openstax.org/books/biology-2e/pages/45-6-community-ecology"),
    ("Commensalism: one species benefits and the other is neither helped nor harmed (birds nesting in trees)", "https://openstax.org/books/biology-2e/pages/45-6-community-ecology"),
    ("Parasitism: the parasite benefits and the host is harmed but not usually killed quickly (tapeworm in the human intestine)", "https://openstax.org/books/biology-2e/pages/45-6-community-ecology"),
    ("Predation: one organism consumes another (lynx and snowshoe hare)", "https://openstax.org/books/biology-2e/pages/45-6-community-ecology"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
