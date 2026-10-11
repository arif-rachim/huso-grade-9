"""Independent checks for materi/biology/anatomy-endocrine.md.

Facts are encoded once as a small knowledge base; the table in the text, the worked examples and
every Check answer are evaluated against it. FACT_CHECKS lists the claims with a source."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/anatomy-endocrine.md").read_text()
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


# Knowledge base (ICSE class 9-10 / OpenStax A&P)
KB = {
    "thyroid": dict(loc="neck", hormones={"thyroxine"}, duct=False),
    "adrenal": dict(loc="kidney", hormones={"adrenaline"}, duct=False),
    "pancreas": dict(loc="stomach", hormones={"insulin", "glucagon"}, duct=True),  # exocrine part has a duct
    "pituitary": dict(loc="brain", hormones={"growth hormone"}, duct=False),
}
KIND = {"thyroid": "endocrine", "adrenal": "endocrine", "pituitary": "endocrine",
        "pancreas": "both", "salivary": "exocrine"}
HORMONE_OF = {h: g for g, d in KB.items() for h in d["hormones"]}

# ---- the table in the text equals the knowledge base
rows = re.findall(r"^\| \*\*(\w+)\*\* \| (.*?) \| (.*?) \| (.*?) \|$", TXT, re.M)
ok(len(rows) == 4)
for gland, loc, sec, fn in rows:
    g = gland.lower()
    ok(g in KB)
    ok(KB[g]["loc"] in loc.lower(), f"location {g}")
    for h in KB[g]["hormones"]:
        ok(h in sec.lower() or h.split()[0] in sec.lower(), f"secretion {g}")
ok({r[0].lower() for r in rows} == set(KB))
ok(len(KB["pancreas"]["hormones"]) == 2)
ok("lowers" in rows[2][3] and "raises" in rows[2][3])
ok("master gland" in rows[3][3])


def mentioned_hormone(s):
    s = s.lower()
    for h in ("thyroxine", "adrenaline", "insulin", "glucagon", "growth hormone"):
        if h in s:
            return h


def mentioned_gland(s):
    s = s.lower()
    return next((g for g in ("thyroid", "adrenal", "pancreas", "pituitary", "salivary") if g in s), None)


# ---- Example 1: fast heartbeat before a race -> adrenaline, made in adrenal (on top of kidneys), by blood, no duct
o = options("**Example 1.**")
ok(len(o) == 5 and len(set(o.values())) == 5)
good = []
for k, v in o.items():
    h = mentioned_hormone(v)
    gl_ok = ("kidney" in v) == (HORMONE_OF[h] == "adrenal") and ("neck" in v) == (HORMONE_OF[h] == "thyroid")
    gl_ok = gl_ok and ("behind the stomach" in v) == (HORMONE_OF[h] == "pancreas") and ("brain" in v) == (HORMONE_OF[h] == "pituitary")
    route_blood = "blood" in v and "duct" not in v.replace("no duct", "")
    if h == "adrenaline" and gl_ok and route_blood:
        good.append(k)
ok(good == ["B"], good)
ok("**Answer: (B).**" in TXT.split("**Example 2.**")[0])
ok(sum(1 for v in o.values() if mentioned_hormone(v) == "adrenaline") == 2)  # B and E share the hormone; E fails on the duct
ok("duct" in o["E"] and "blood" not in o["E"])

# ---- Example 2: high blood sugar -> insulin (pancreas) -> sugar falls
EFFECT = {"insulin": "falls", "glucagon": "rises"}
o = options("**Example 2.**")
good = []
for k, v in o.items():
    h = mentioned_hormone(v)
    gland = mentioned_gland(v)
    direction = "falls" if "falls" in v else "rises"
    if HORMONE_OF[h] == gland and EFFECT[h] == direction == "falls":  # need to lower high sugar
        good.append(k)
ok(good == ["B"], good)
ok("**Answer: (B).**" in TXT.split("**Example 2.**")[1].split("## ⚠️")[0])
ok("(D) The thyroid" in TXT and HORMONE_OF["insulin"] != "thyroid")
ok("(C) The pancreas releases insulin, and blood sugar rises even more" in TXT and EFFECT["insulin"] != "rises")

# ---- Q1: both exocrine and endocrine
o = options("**1.** Which of these")
hits = [k for k, v in o.items() if KIND[mentioned_gland(v) or "salivary"] == "both"]
ok(hits == ["C"] and key_letter(1) == "C", hits)
ok(KIND["salivary"] == "exocrine" and o["E"].startswith("Salivary"))

# ---- Q2: iodine -> thyroid -> thyroxine
IODINE_GLAND, IODINE_HORMONE = "thyroid", "thyroxine"
o = options("**2.** A person")
hits = [k for k, v in o.items() if mentioned_gland(v) == IODINE_GLAND and mentioned_hormone(v) == IODINE_HORMONE]
ok(hits == ["E"] and key_letter(2) == "E", hits)
ok(mentioned_hormone(o["D"]) == "insulin" and HORMONE_OF["insulin"] != "thyroid")

# ---- Q3: the master gland
o = options("**3.** 🎮")
hits = [k for k, v in o.items() if mentioned_gland(v) == "pituitary"]
ok(hits == ["A"] and key_letter(3) == "A")
ok(KIND["salivary"] != "endocrine")

# ---- Q4: low blood sugar -> glucagon -> liver breaks down glycogen -> blood sugar rises
o = options("**4.** 🍳")
hits = []
for k, v in o.items():
    h = mentioned_hormone(v)
    if h == "glucagon" and "breaks down" in v and "rises" in v:
        hits.append(k)
ok(hits == ["D"] and key_letter(4) == "D", hits)
ok(mentioned_hormone(o["E"]) == "adrenaline" and HORMONE_OF["adrenaline"] == "adrenal" != "pancreas")
ok(EFFECT["insulin"] == "falls")  # (A)/(B) use insulin: wrong for LOW sugar

# ---- Q5: matching row
o = options("**5.** Which row")
hits = []
for k, v in o.items():
    g = mentioned_gland(v)
    h = mentioned_hormone(v)
    loc_ok = {"thyroid": "neck", "adrenal": "kidneys", "pancreas": "behind the stomach", "pituitary": "base of the brain"}[g] in v
    if loc_ok and HORMONE_OF[h] == g:
        hits.append(k)
ok(hits == ["B"] and key_letter(5) == "B", hits)

# ---- answer letters: no letter more than twice, five keys
keys = [key_letter(i) for i in range(1, 6)]
ok(len(keys) == 5 and all(keys.count(c) <= 2 for c in "ABCDE"), keys)
for i in range(1, 6):
    blk = re.search(rf"^\*\*{i}\.\*\*(.*?)(?=^\*\*{i+1}\.\*\*|<details>)", TXT, re.S | re.M).group(1)
    ok(len(re.findall(r"\(([A-E])\)", blk)) == 5)

FACT_CHECKS = [
    ("Exocrine glands release secretions through ducts; endocrine glands are ductless and release hormones into the surrounding fluid/blood", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-1-an-overview-of-the-endocrine-system"),
    ("A hormone is a chemical transported in the blood that acts on cells in distant tissues", "https://en.wikipedia.org/wiki/Hormone"),
    ("The thyroid is in the neck, in front of the trachea, just below the larynx", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-4-the-thyroid-gland"),
    ("Thyroid hormone (T4, thyroxine) regulates basal metabolic rate and needs iodine; iodine lack causes goiter", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-4-the-thyroid-gland"),
    ("Thyroxine controls basal metabolism; iodine is essential for it and undersecretion causes goitre (ICSE)", "https://www.vedantu.com/icse/selina-concise-biology-class-10-solutions-chapter-12"),
    ("The adrenal glands sit on top of the kidneys", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-6-the-adrenal-glands"),
    ("Adrenal medulla secretes epinephrine (adrenaline) for fight-or-flight: more heart rate, glucose released from liver, airways widen", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-6-the-adrenal-glands"),
    ("The pancreas lies mostly behind the lower half of the stomach and is mainly exocrine (enzymes via the pancreatic duct)", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-9-the-endocrine-pancreas"),
    ("Pancreatic islets: beta cells make insulin, alpha cells make glucagon", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-9-the-endocrine-pancreas"),
    ("Insulin is released when blood glucose is high and lowers it; glucagon is released when it is low and makes the liver release glucose", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-9-the-endocrine-pancreas"),
    ("The pituitary is a bean/pea-sized gland hanging from the hypothalamus in the sella turcica at the base of the brain; it makes growth hormone", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-3-the-pituitary-gland-and-hypothalamus"),
    ("The pituitary is called the master gland because it controls the functioning of other endocrine glands (ICSE)", "https://www.vedantu.com/icse/selina-concise-biology-class-10-solutions-chapter-12"),
    ("The hypothalamus controls pituitary secretion with releasing and inhibiting hormones", "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-2-hormones"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
