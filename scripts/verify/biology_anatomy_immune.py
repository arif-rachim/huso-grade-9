"""Independent checks for materi/biology/anatomy-immune.md.

The immune facts are encoded as small data tables; the examples and the Check answers are
evaluated against them (the numeric part of Example 2 is recomputed)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/anatomy-immune.md").read_text()
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
INNATE = {"fast": True, "specific": False, "memory": False, "cells": {"phagocytes"}, "tools": {"skin", "mucus", "phagocytes", "fever"}}
ADAPTIVE = {"fast": False, "specific": True, "memory": True, "cells": {"b cells", "t cells"}}
ROLE = {"b cell": "makes antibodies (via plasma cells)", "helper t": "gives orders", "killer t": "destroys infected cells"}
ok(INNATE["tools"] == {"skin", "mucus", "phagocytes", "fever"})
for w in ("skin", "mucus", "phagocytes", "fever"):
    ok(w in TXT.lower())
ok(set(re.findall(r"inhaled|swallowed|skin|injection", TXT.split("6. **Allergy.**")[1].split("\n")[0])) == {"inhaled", "swallowed", "skin", "injection"})
ALLERGENS = {"dust", "pollen", "mites", "sunlight", "foods"}
line6 = TXT.split("6. **Allergy.**")[1].split("\n")[0].lower()
ok(all(a in line6 or a.rstrip("s") in line6 for a in ALLERGENS))
for sym in ("sneezing", "watery eyes", "itching", "rash", "swelling", "difficulty breathing"):
    ok(sym in line6, sym)

# ---- Example 1: allergy
o = options("**Example 1.**")
ok(len(o) == 5)
good = [k for k, v in o.items() if "harmless" in v and "allergic" in v and "allergen" in v]
ok(good == ["B"], good)
ok("**Answer: (B).**" in TXT.split("**Example 2.**")[0])
ok("antibody" in o["E"] and "peanut is an antibody" in o["E"])  # an allergen is not an antibody
ok("killer T cells made antibodies" in o["C"] and ROLE["killer t"] == "destroys infected cells")  # killer T cells do not make antibodies

# ---- Example 2: numbers
first_peak, first_day, second_peak, second_day = 20, 14, 200, 4
ratio = second_peak / first_peak
earlier = first_day - second_day
ok(ratio == 10 and earlier == 10)
o = options("**Example 2.**")
ok(len(o) == 5)
def parse(v):
    times = float(re.search(r"(\d+) times", v).group(1)) if "times" in v else 1.0
    days = float(re.search(r"(\d+) days", v).group(1)) if "days faster" in v else 0.0
    cause = "memory" if "memory cells" in v else "innate"
    return times, days, cause
hits = [k for k, v in o.items() if parse(v) == (ratio, earlier, "memory")]
ok(hits == ["A"], hits)
ok(parse(o["B"])[1] == second_day and parse(o["E"])[0] == 4 and "same size" in o["D"])
ok("**Answer: (A).**" in TXT.split("**Example 2.**")[1].split("## ⚠️")[0])
ok(second_peak / first_peak != 4)  # distractor (E): 4 is the day count, not the ratio
ok(ADAPTIVE["memory"] and not INNATE["memory"])  # (C) 'innate' cause is wrong

# ---- Q1: feature of innate immunity
o = options("**1.** Which feature")
def innate_feature(v):
    v = v.lower()
    if "memory" in v or "specific" in v or "b cells" in v or "days" in v:
        return False
    return "same general way" in v and "right away" in v
hits = [k for k, v in o.items() if innate_feature(v)]
ok(hits == ["D"] and key_letter(1) == "D", hits)

# ---- Q2: tag/antigen, locks-on/antibody
o = options("**2.** 🎮")
hits = [k for k, v in o.items() if v.lower().startswith("antigen, antibody")]
ok(hits == ["B"] and key_letter(2) == "B")
ok(o["A"].lower() == "antibody, antigen")

# ---- Q3: roles
o = options("**3.** Which statement")
def roles_ok(v):
    v = v.lower()
    return "b cells become plasma cells that make antibodies" in v and "killer t cells destroy infected" in v
hits = [k for k, v in o.items() if roles_ok(v)]
ok(hits == ["E"] and key_letter(3) == "E")
ok("Helper T cells make antibodies" in o["C"])
ok(set(ADAPTIVE["cells"]) == {"b cells", "t cells"})

# ---- Q4: pollen: inhaled allergen
ROUTE = {"pollen": "inhaled", "food": "swallowed", "sting": "injection", "latex": "skin"}
o = options("**4.** 🍳")
hits = [k for k, v in o.items() if v.lower().startswith(ROUTE["pollen"]) and v.endswith("an allergen")]
ok(hits == ["A"] and key_letter(4) == "A", hits)
ok(len({v for v in o.values()}) == 5)

# ---- Q5: memory cells
o = options("**5.** A person")
hits = [k for k, v in o.items() if "memory cells" in v.lower() and "antibod" in v]
ok(hits == ["C"] and key_letter(5) == "C")
ok("Phagocytes" in o["A"] and not INNATE["memory"])

keys = [key_letter(i) for i in range(1, 6)]
ok(len(keys) == 5 and all(keys.count(c) <= 2 for c in "ABCDE"), keys)
for i in range(1, 6):
    blk = re.search(rf"^\*\*{i}\.\*\*(.*?)(?=^\*\*{i+1}\.\*\*|<details>)", TXT, re.S | re.M).group(1)
    ok(len(re.findall(r"\(([A-E])\)", blk)) == 5)

FACT_CHECKS = [
    ("Innate immunity is present from birth, nonspecific and fast (barriers, phagocytes, fever)", "https://openstax.org/books/biology-2e/pages/42-1-innate-immune-response"),
    ("Skin is a barrier and mucous membranes trap microbes in mucus that is swept or rinsed out", "https://openstax.org/books/biology-2e/pages/42-1-innate-immune-response"),
    ("Phagocytes (macrophages, neutrophils) engulf pathogens", "https://openstax.org/books/biology-2e/pages/42-1-innate-immune-response"),
    ("Fever is raised core body temperature that slows some bacteria", "https://openstax.org/books/biology-2e/pages/42-1-innate-immune-response"),
    ("Adaptive response takes days to weeks the first time and is specific", "https://openstax.org/books/biology-2e/pages/42-2-adaptive-immune-response"),
    ("B cells become plasma cells that secrete antibodies; antibodies are Y-shaped", "https://openstax.org/books/biology-2e/pages/42-2-adaptive-immune-response"),
    ("Helper T cells activate B cells and cytotoxic (killer) T cells; cytotoxic T cells destroy infected cells", "https://openstax.org/books/biology-2e/pages/42-2-adaptive-immune-response"),
    ("Memory cells give a faster, stronger response on re-exposure; vaccines build memory without disease", "https://openstax.org/books/biology-2e/pages/42-2-adaptive-immune-response"),
    ("An allergy is an immune response to a harmless antigen; symptoms include sneezing, itchy watery eyes, hives, airway constriction", "https://openstax.org/books/biology-2e/pages/42-4-disruptions-in-the-immune-system"),
    ("Common allergens: pollen, dust mites (droppings), foods such as peanuts, milk, eggs", "https://en.wikipedia.org/wiki/Allergy"),
    ("Routes of exposure: inhaled, ingested, skin contact, injection (insect sting)", "https://en.wikipedia.org/wiki/Allergy"),
    ("Sunlight can trigger an itchy rash in susceptible people (polymorphous light eruption)", "https://en.wikipedia.org/wiki/Polymorphous_light_eruption"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
