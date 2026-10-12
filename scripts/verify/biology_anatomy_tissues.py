"""Independent checks for materi/biology/anatomy-tissues.md.

The tissue facts are a lookup table; the markdown tables are compared with it, and every
example/Check option is evaluated against it (the 'how many striated' count is recomputed)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/anatomy-tissues.md").read_text()
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


# ---- knowledge base
CONNECTIVE = {
    "bone": dict(loc="skeleton", joins=None),
    "cartilage": dict(loc="joints", joins=None),
    "blood": dict(loc="vessels", joins=None),
    "ligament": dict(loc="joint", joins=("bone", "bone")),
    "tendon": dict(loc="muscle", joins=("muscle", "bone")),
}
MUSCLE = {
    "skeletal": dict(striated=True, voluntary=True, loc="bones"),
    "smooth": dict(striated=False, voluntary=False, loc="stomach"),
    "cardiac": dict(striated=True, voluntary=False, loc="heart"),
}
GROUP = {"bone": "connective", "cartilage": "connective", "blood": "connective", "ligament": "connective",
         "tendon": "connective", "skeletal": "muscular", "smooth": "muscular", "cardiac": "muscular"}
ok(sum(m["striated"] for m in MUSCLE.values()) == 2)
ok(sum(m["voluntary"] for m in MUSCLE.values()) == 1)
ok(CONNECTIVE["ligament"]["joins"] == ("bone", "bone") and CONNECTIVE["tendon"]["joins"] == ("muscle", "bone"))

# ---- markdown tables vs KB
rows = re.findall(r"^\| \*\*(\w+)\*\* \| (.*?) \| (.*?) \|$", TXT, re.M)
conn = {r[0].lower(): r for r in rows if r[0].lower() in CONNECTIVE}
ok(set(conn) == set(CONNECTIVE))
for name, d in CONNECTIVE.items():
    ok(d["loc"] in conn[name][1].lower(), name)
ok("bone to bone" in conn["ligament"][2] and "muscle to bone" in conn["tendon"][2])
mrows = re.findall(r"^\| \*\*(.*?)\*\*(?: \((.*?)\))? \| (.*?) \| (.*?) \| (.*?) \|$", TXT, re.M)
ok(len(mrows) == 3)
alias = {"Striated": "skeletal", "Unstriated": "smooth", "Cardiac": "cardiac"}
for nm, par, loc, ctrl, fn in mrows:
    m = MUSCLE[alias[nm]]
    ok(m["loc"] in loc.lower(), nm)
    ok((ctrl == "voluntary") == m["voluntary"])
    ok(ctrl in ("voluntary", "involuntary"))
ok(TXT.count("Striated** (striped)") == 1)

# ---- Example 1 (butcher)
steak, cord, tip = "muscle", ("muscle", "bone"), "bendy"
def name_cord(j):
    return [k for k, v in CONNECTIVE.items() if v["joins"] == j][0]
ok(name_cord(cord) == "tendon")
o = options("**Example 1.**")
ok(len(o) == 5)
hits = [k for k, v in o.items() if [x.strip().lower() for x in v.split(",")] == ["muscle", name_cord(cord), "cartilage"]]
ok(hits == ["A"], hits)
ok("**Answer: (A).**" in TXT.split("**Example 2.**")[0])
ok("ligament" in o["B"] and "bone" in o["C"].split(",")[2] and o["E"].lower().split(",")[1].strip() == "cartilage")

# ---- Example 2 (swimmer)
truth = {"X": "skeletal", "Y": "cardiac", "Z": "smooth"}  # arm voluntary / heart / stomach wall
striated_count = sum(MUSCLE[v]["striated"] for v in truth.values())
ok(striated_count == 2)
o = options("**Example 2.**")
hits = []
for k, v in o.items():
    names = dict(re.findall(r"([XYZ]) (\w+)", v))
    count = int(re.search(r"(\d) striated", v).group(1))
    claimed = sum(MUSCLE[names[x]]["striated"] for x in "XYZ")
    ok(claimed == count or k in "BC", (k, claimed, count))  # B and C are the wrong-count distractors
    if names == truth and count == striated_count:
        hits.append(k)
ok(hits == ["A"], hits)
ok("**Answer: (A).**" in TXT.split("**Example 2.**")[1].split("## ⚠️")[0])
ok(int(re.search(r"(\d) striated", o["B"]).group(1)) == 1 and int(re.search(r"(\d) striated", o["C"]).group(1)) == 3)

# ---- Q1: joins bone to bone
o = options("**1.** Which tissue")
hits = [k for k, v in o.items() if v.strip().lower() in CONNECTIVE and CONNECTIVE[v.strip().lower()]["joins"] == ("bone", "bone")]
ok(hits == ["B"] and key_letter(1) == "B", hits)

# ---- Q2: cord muscle->bone
o = options("**2.** 🍳")
hits = []
for k, v in o.items():
    nm, grp = [x.strip().lower() for x in v.split(";")]
    if nm in CONNECTIVE and CONNECTIVE[nm]["joins"] == ("muscle", "bone") and grp.startswith(GROUP[nm]):
        hits.append(k)
ok(hits == ["D"] and key_letter(2) == "D", hits)
ok(GROUP["tendon"] == "connective")

# ---- Q3: heart muscle
o = options("**3.** 🏊")
hits = []
for k, v in o.items():
    t_ = re.match(r"It is (\w+) muscle", v).group(1)
    vol = "involuntary" in v
    claim_vol = ("voluntary" in v) and not vol
    if t_ == "cardiac" and (MUSCLE["cardiac"]["voluntary"] == claim_vol):
        hits.append(k)
ok(hits == ["A"] and key_letter(3) == "A", hits)
ok("tendons" in o["E"] and MUSCLE["smooth"]["loc"] != "bones")

# ---- Q4: epithelial
EPI = {"loc": "surface", "fn": "protect"}
o = options("**4.** Which statement")
hits = [k for k, v in o.items() if "covers" in v and "lines" in v and "protects" in v]
ok(hits == ["E"] and key_letter(4) == "E")
ok("muscle to bone" in o["A"] or "joins muscle to bone" in o["A"])

# ---- Q5: connective row
o = options("**5.** Which row")
hits = []
for k, v in o.items():
    nm = v.split(":")[0].strip().lower()
    rest = v.split(":", 1)[1]
    loc_fn = rest.lower()
    good = False
    if nm == "cartilage":
        good = "ends of bones" in loc_fn and "flexible" in loc_fn
    elif nm == "tendon":
        good = "muscle to bone" in loc_fn
    elif nm == "ligament":
        good = "bone to bone" in loc_fn
    elif nm == "blood":
        good = "vessels" in loc_fn
    elif nm == "bone":
        good = "skeleton" in loc_fn
    if good:
        hits.append(k)
ok(hits == ["C"] and key_letter(5) == "C", hits)
ok("attaches muscle to bone" in o["D"] and CONNECTIVE["ligament"]["joins"] != ("muscle", "bone"))
ok("joins bone to bone" in o["E"] and CONNECTIVE["tendon"]["joins"] != ("bone", "bone"))

keys = [key_letter(i) for i in range(1, 6)]
ok(len(keys) == 5 and all(keys.count(c) <= 2 for c in "ABCDE"), keys)
for i in range(1, 6):
    blk = re.search(rf"^\*\*{i}\.\*\*(.*?)(?=^\*\*{i+1}\.\*\*|<details>)", TXT, re.S | re.M).group(1)
    ok(len(re.findall(r"\(([A-E])\)", blk)) == 5)

FACT_CHECKS = [
    ("Epithelial tissue covers body surfaces (skin, airways, digestive tract), lines organs and forms glands; it protects, absorbs and secretes", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-2-epithelial-tissue"),
    ("Bone supports and protects internal organs", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-3-connective-tissue-supports-and-protects"),
    ("Cartilage is in the rib cage, nose, joint surfaces and external ear; it is strong yet flexible and cushions", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-3-connective-tissue-supports-and-protects"),
    ("Blood is a connective tissue that circulates in vessels carrying oxygen, defending against pathogens and clotting", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-3-connective-tissue-supports-and-protects"),
    ("A tendon is a band of fibrous connective tissue that attaches a muscle to a bone", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-3-connective-tissue-supports-and-protects"),
    ("A ligament is fibrous connective tissue that connects bones to other bones", "https://en.wikipedia.org/wiki/Ligament"),
    ("Skeletal muscle is striated and voluntary, attached to bones; moves the body", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-4-muscle-tissue-and-motion"),
    ("Smooth muscle is non-striated and involuntary, in walls of the digestive tract, airways and arteries", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-4-muscle-tissue-and-motion"),
    ("Cardiac muscle is striated, branched and involuntary, found in the heart wall, and pumps blood", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-4-muscle-tissue-and-motion"),
    ("Skeletal muscle also generates body heat", "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-4-muscle-tissue-and-motion"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
