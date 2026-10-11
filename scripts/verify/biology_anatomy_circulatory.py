"""Independent checks for materi/biology/anatomy-circulatory.md.

* the route of the blood is a directed graph; every route option of Example 1 is checked edge by edge,
* the ABO rules are computed from antigens and antibodies (donor/recipient table, universal donor/acceptor),
  and Example 2 and Check question 4 are brute-forced from that table,
* heart rate x stroke volume and every distractor of question 2 are recomputed,
* the vessel table (oxygen level) is data and question 3 is tested against it."""
import pathlib, re
from itertools import product

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/anatomy-circulatory.md").read_text()
n = 0

def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1

def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    return dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))

def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", TXT.split("<details>")[1], re.M).group(1)

# ---------------------------------------------------------------- heart route as a graph
# (node, node, valve met on the edge or None)
EDGES = [
    ("body", "vena cava", None), ("vena cava", "right atrium", None),
    ("right atrium", "right ventricle", "tricuspid valve"),
    ("right ventricle", "pulmonary trunk", "pulmonary valve"),
    ("pulmonary trunk", "lungs", None), ("lungs", "pulmonary veins", None),
    ("pulmonary veins", "left atrium", None),
    ("left atrium", "left ventricle", "bicuspid valve"),
    ("left ventricle", "aorta", "aortic valve"), ("aorta", "body", None),
]
ADJ = {}
for a, b, v in EDGES:
    ADJ.setdefault(a, {})[b] = v

def route_ok(seq):
    return all(b in ADJ.get(a, {}) for a, b in zip(seq, seq[1:]))

def valves(seq):
    return [ADJ[a][b] for a, b in zip(seq, seq[1:]) if ADJ[a][b]]

# full path claimed in the text
FULL = "vena cava → right atrium → tricuspid valve → right ventricle → pulmonary valve → pulmonary trunk → lungs → pulmonary veins → left atrium → bicuspid valve → left ventricle → aortic valve → aorta → body → vena cava"
ok(FULL in TXT)
cycle = ["vena cava", "right atrium", "right ventricle", "pulmonary trunk", "lungs", "pulmonary veins", "left atrium", "left ventricle", "aorta", "body", "vena cava"]
ok(route_ok(cycle) and valves(cycle) == ["tricuspid valve", "pulmonary valve", "bicuspid valve", "aortic valve"])
# double circulation: the cycle passes the heart (atrium+ventricle) twice: right side then left side
ok(sum(1 for x in cycle if x.endswith("ventricle")) == 2 and sum(1 for x in cycle if x.endswith("atrium")) == 2)
# pulmonary loop: RV -> lungs -> LA ; systemic loop: LV -> body -> RA
ok(route_ok(["right ventricle", "pulmonary trunk", "lungs", "pulmonary veins", "left atrium"]))
ok(route_ok(["left ventricle", "aorta", "body", "vena cava", "right atrium"]))

# ---------------------------------------------------------------- Example 1
def parse_route(s):
    return [x.strip() for x in s.split("→")]
o = options("**Example 1.**")
ok(len(set(o.values())) == 5)
def with_start(s):                      # every option starts after the right ventricle
    seq = ["right ventricle"] + parse_route(s)
    return seq
results = {}
for k, v in o.items():
    seq = with_start(v)
    # the options skip valves: valves between atrium and ventricle are not written, so allow the same edges
    results[k] = route_ok(seq) and seq[-1] == "aorta"
ok(results == {"A": True, "B": False, "C": False, "D": False, "E": False}, results)
ok(valves(with_start(o["A"])) == ["pulmonary valve", "bicuspid valve", "aortic valve"] and "**3**" in TXT)
# trap reasons
ok("right atrium" not in ADJ["pulmonary veins"] and "left atrium" in ADJ["pulmonary veins"])         # (D)
ok("right atrium" in ADJ["vena cava"] and "lungs" not in ADJ["vena cava"] and "vena cava" not in ADJ["lungs"])  # (C)
ok("left ventricle" not in ADJ.get("right ventricle", {}))                                            # (E): nothing crosses the septum
ok("pulmonary trunk" not in ADJ["pulmonary veins"] and "pulmonary veins" in ADJ["lungs"] and "pulmonary trunk" in ADJ["right ventricle"])  # (B) is backwards

# ---------------------------------------------------------------- ABO from first principles
ANTIGENS = {"A": {"A"}, "B": {"B"}, "AB": {"A", "B"}, "O": set()}
ANTIBODIES = {g: ({"A", "B"} - ag) for g, ag in ANTIGENS.items()}      # plasma has antibodies against antigens you lack
ok(ANTIBODIES == {"A": {"B"}, "B": {"A"}, "AB": set(), "O": {"A", "B"}})
def can_give(donor, recipient):
    """red cells are safe if no antigen on the donor cells is attacked by the recipient's antibodies"""
    return not (ANTIGENS[donor] & ANTIBODIES[recipient])
TABLE = {d: [r for r in ("A", "B", "AB", "O") if can_give(d, r)] for d in ("O", "A", "B", "AB")}
ok(TABLE == {"O": ["A", "B", "AB", "O"], "A": ["A", "AB"], "B": ["B", "AB"], "AB": ["AB"]}, TABLE)
svg_abo = (ROOT / "public/content/biology/circulatory-abo.svg").read_text()
for d, rs in TABLE.items():
    ok(f"→ {', '.join(rs)}" in svg_abo, d)
ok("Antigens: A and B" in svg_abo and "anti-A + anti-B" in svg_abo)
universal_donor = [d for d in ANTIGENS if all(can_give(d, r) for r in ANTIGENS)]
universal_acceptor = [r for r in ANTIGENS if all(can_give(d, r) for d in ANTIGENS)]
ok(universal_donor == ["O"] and universal_acceptor == ["AB"])

# Example 2: donors for a group A patient
donors_for_A = [d for d in ANTIGENS if can_give(d, "A")]
ok(sorted(donors_for_A) == ["A", "O"])
o = options("**Example 2.**")
ok(len(set(o.values())) == 5 and o["B"] == "A and O")
ok(o["A"] == "A only" and o["C"] == "A and AB" and o["D"] == "B and O" and o["E"] == "O only")
ok(not can_give("AB", "A") and not can_give("B", "A") and can_give("O", "A") and can_give("A", "A"))

# Q4: squad
squad = ["A", "B", "AB", "O", "O"]
patient_idx = squad.index("B")
others = squad[:patient_idx] + squad[patient_idx + 1:]
count = sum(can_give(d, "B") for d in others)
ok(count == 2)
o = options("**4.**")
ok(o["C"] == "2" and len(set(o.values())) == 5)
ok(sum(d in ("B", "O") for d in others) == 2 and sum(d == "O" for d in others) == 2)
ok(sum(d in ("O",) for d in others) - 1 == 1)             # only one O -> 1 (distractor B)
ok(len(others) == 4 and sum(d in ("AB", "B", "O") for d in others) == 3)   # counting AB too -> 3 (distractor D)
ok(key_letter(4) == "C")

# ---------------------------------------------------------------- Q2: pulse
beats_15s = 40
bpm = beats_15s * (60 // 15)
ml = 80
out_ml = bpm * ml
ok(bpm == 160 and out_ml == 12800 and out_ml / 1000 == 12.8)
o = options("**2.**")
ok(o["A"] == "12.8 L/min" and len(set(o.values())) == 5)
ok(beats_15s * ml / 1000 == 3.2 and o["B"] == "3.2 L/min")            # forgot x4
ok(out_ml / 10000 == 1.28 and o["C"] == "1.28 L/min")                 # decimal slip
ok(o["D"] == "160 L/min" and o["E"] == "12,800 L/min")                # pulse alone; unit slip
ok(key_letter(2) == "A")
# the 'hook' numbers: 160 vs a resting 70 bpm
ok("160 beats" in TXT and "70" in TXT)

# ---------------------------------------------------------------- Q3: vessel table
VESSELS = {  # oxygen: True = high
    "aorta": True, "pulmonary trunk": False, "pulmonary artery": False, "pulmonary vein": True,
    "vena cava": False, "coronary artery": True, "coronary vein": False,
}
rows = re.findall(r"^\| \*\*(.+?)\*\*.*?\| (high|low) \((?:red|blue)\) \|$", TXT, re.M)
tab = {k.lower(): v == "high" for k, v in rows}
ok(tab["aorta"] and not tab["pulmonary trunk"] and tab["pulmonary veins"] and not tab["vena cava"] and tab["coronary artery"] and not tab["coronary vein"])
o = options("**3.**")
good = [k for k, v in o.items() if VESSELS[v.lower()]]
ok(good == ["B"] and key_letter(3) == "B" and len(set(o.values())) == 5)
# arteries vs veins by direction, not by oxygen: the two pulmonary vessels break the oxygen rule
ok(not VESSELS["pulmonary artery"] and VESSELS["pulmonary vein"])

# ---------------------------------------------------------------- Q1, Q5 (concept) and structure facts
o = options("**1.**")
ok(o["D"] == "Bicuspid valve" and key_letter(1) == "D" and len(set(o.values())) == 5)
valve_between = {("left atrium", "left ventricle"): "bicuspid valve"}
ok(ADJ["left atrium"]["left ventricle"] == "bicuspid valve" and ADJ["right atrium"]["right ventricle"] == "tricuspid valve")
o = options("**5.**")
ok(o["E"].startswith("Lymph flows in one direction") and key_letter(5) == "E" and len(set(o.values())) == 5)
ok(sum(t in TXT for t in ("**Palpitations:**", "**Cardiac arrest:**", "**Hypertension:**")) == 3)
ok("120/80" in TXT)

keys = [key_letter(q) for q in range(1, 6)]
ok(keys == ["D", "A", "B", "C", "E"] and max(keys.count(c) for c in "ABCDE") <= 2)
for q in range(1, 6):
    ok(len(options(f"**{q}.**")) == 5)

FACT_CHECKS = [
    ("The heart has four chambers; tricuspid valve (right AV), mitral/bicuspid (left AV), pulmonary and aortic valves at the exits; left ventricle has the thickest wall", "https://en.wikipedia.org/wiki/Heart"),
    ("Blood path: vena cava -> right atrium -> tricuspid -> right ventricle -> pulmonary valve -> lungs -> pulmonary veins -> left atrium -> mitral -> left ventricle -> aortic valve -> aorta", "https://en.wikipedia.org/wiki/Heart"),
    ("Double circulation: pulmonary circuit to the lungs and systemic circuit to the body", "https://openstax.org/books/biology-2e/pages/40-1-overview-of-the-circulatory-system"),
    ("Pulmonary veins carry oxygen-rich blood from the lungs to the left atrium", "https://en.wikipedia.org/wiki/Heart"),
    ("Coronary arteries arise from the aorta just above the aortic valve and supply the heart muscle; coronary veins carry low-oxygen blood back to the right atrium", "https://en.wikipedia.org/wiki/Coronary_circulation"),
    ("ABO: A has A antigen and anti-B; B has B antigen and anti-A; O has neither antigen and anti-A and anti-B", "https://en.wikipedia.org/wiki/ABO_blood_group_system"),
    ("Type O is the universal donor and type AB the universal acceptor (red cells, ABO view)", "https://openstax.org/books/biology-2e/pages/40-2-components-of-the-blood"),
    ("Palpitations: heartbeat that feels irregular, forceful, fluttering or pounding", "https://www.nhlbi.nih.gov/health/arrhythmias/symptoms"),
    ("Cardiac arrest: the heart suddenly and unexpectedly stops pumping", "https://www.nhlbi.nih.gov/health/cardiac-arrest"),
    ("A heart attack is a blockage that cuts the blood supply to part of the heart muscle (different from cardiac arrest)", "https://www.nhlbi.nih.gov/health/heart-attack"),
    ("Hypertension: blood pushes on artery walls with consistently excessive force; normal is under 120/80 mm Hg", "https://www.nhlbi.nih.gov/health/high-blood-pressure"),
    ("Lymph returns tissue fluid to the blood, flows one way through nodes and valves to the subclavian veins, moved by muscle contraction (no central pump), lacteals absorb fat", "https://en.wikipedia.org/wiki/Lymphatic_system"),
    ("Cardiac output = heart rate x stroke volume; about 5 L/min at rest, stroke volume about 70 mL at 70 beats/min", "https://en.wikipedia.org/wiki/Cardiac_output"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
