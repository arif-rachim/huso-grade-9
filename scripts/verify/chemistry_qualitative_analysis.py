"""Independent checks for materi/chemistry/analytical-qualitative.md.
Method: encode the evidence table once as data, then deduce every answer by elimination; plus a Ksp/Kf calculation
for the silver halide + ammonia clue."""
import math, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk

C = Chk("materi/chemistry/analytical-qualitative.md")
ok = C.ok

# ---- evidence table (school level, the same one drawn in analytical-ion-tests.svg)
# ion: (NaOH drops, NaOH excess, NH3 drops, NH3 excess)
CAT = {
    "Cu2+": ("pale blue", "insoluble", "pale blue", "dissolves"),
    "Fe2+": ("green", "insoluble", "green", "insoluble"),
    "Fe3+": ("red-brown", "insoluble", "red-brown", "insoluble"),
    "Al3+": ("white", "dissolves", "white", "insoluble"),
    "Zn2+": ("white", "dissolves", "white", "dissolves"),
    "Mg2+": ("white", "insoluble", "white", "insoluble"),
    "Ca2+": ("white", "insoluble", "none", "-"),
}
FLAME = {"Li+": "crimson", "Na+": "yellow", "K+": "lilac", "Ca2+": "orange-red", "Sr2+": "scarlet",
         "Ba2+": "apple green", "Cu2+": "blue-green"}


def candidates(**obs):
    idx = {"naoh": 0, "naoh_x": 1, "nh3": 2, "nh3_x": 3}
    return sorted(i for i, row in CAT.items() if all(row[idx[k]] == v for k, v in obs.items()))


# Example 1
c = candidates(naoh="white", naoh_x="dissolves", nh3="white", nh3_x="insoluble")
ok(c == ["Al3+"], c)
o = C.options("**Example 1.**")
ok({k: v for k, v in o.items()} == {"A": "Zn²⁺", "B": "Mg²⁺", "C": "Ca²⁺", "D": "Al³⁺", "E": "Fe³⁺"})
ok("**Answer: (D).**" in C.txt.split("**Example 1.**")[1].split("**Example 2.**")[0])
ok(candidates(naoh="white", naoh_x="dissolves") == ["Al3+", "Zn2+"])               # step 3
ok(candidates(naoh="white", naoh_x="dissolves", nh3_x="dissolves") == ["Zn2+"])    # "Zn would dissolve"

# ---- silver halides in ammonia: Ksp * Kf says how much dissolves in NH3 (independent of the colour story)
KF = 1.1e7
KSP = {"Cl-": 1.8e-10, "Br-": 5.0e-13, "I-": 8.3e-17}
# AgX + 2 NH3 <-> Ag(NH3)2+ + X-,  K = Ksp*Kf,  s = sqrt(K) * [NH3]
S = {x: math.sqrt(k * KF) for k, x in zip(KSP.values(), KSP)}       # per 1 M NH3
need = 0.01   # a typical test precipitate is about 0.01 mol per liter of test mixture
dilute = {x: s * 1.0 > need for x, s in S.items()}                  # dilute (about 1-2 M) ammonia
ok(dilute == {"Cl-": True, "Br-": False, "I-": False}, S)
ok(S["Br-"] * 10 > need)          # concentrated NH3 (about 10 M) does dissolve AgBr
ok(S["I-"] * 10 < need)           # but not AgI
AGX = {"Cl-": "white", "Br-": "cream", "I-": "yellow"}

# Example 2: build each salt and test it against the observations
salts = {"A": ("K+", "Cl-"), "B": ("K+", "Br-"), "C": ("Na+", "I-"), "D": ("K+", "I-"), "E": ("K+", "CO32-")}
matches = []
for k, (cat, an) in salts.items():
    if FLAME[cat] != "lilac":          # lilac through cobalt glass = K+ (Na+ would be blocked by the glass)
        continue
    if AGX.get(an) == "yellow" and not dilute[an] and S[an] * 10 < need:   # yellow and insoluble in ammonia
        matches.append(k)
ok(matches == ["D"], matches)
ok(C.options("**Example 2.**") == {"A": "KCl", "B": "KBr", "C": "NaI", "D": "KI", "E": "K₂CO₃"})
ok("**Answer: (D).**" in C.txt.split("**Example 2.**")[1].split("## ⚠️")[0])

# Q1: yellow + lilac through cobalt glass
combos = {"A": {"Li+", "Ca2+"}, "B": {"Na+", "K+"}, "C": {"Na+", "Cu2+"}, "D": {"K+", "Ba2+"}, "E": {"Li+", "Na+"}}
good = [k for k, s in combos.items() if {FLAME[i] for i in s} >= {"yellow", "lilac"}]
ok(good == ["B"], good)
ok(C.options("**1.**")["B"] == "Na⁺ and K⁺" and C.key_letter(1) == "B")

# Q2: gas + limewater -> carbonate; the other anions give no gas with dilute acid
GAS_WITH_ACID = {"Cl-": None, "SO42-": None, "I-": None, "CO32-": "CO2", "Br-": None}
ok([a for a, g in GAS_WITH_ACID.items() if g == "CO2"] == ["CO32-"])
ok(C.options("**2.**")["D"] == "CO₃²⁻" and C.key_letter(2) == "D")

# Q3: green ppt, insoluble in excess NaOH (and goes brown in air: Fe2+ -> Fe3+)
g = [i for i, r in CAT.items() if r[0] == "green" and r[1] == "insoluble"]
ok(g == ["Fe2+"])
ok(C.options("**3.**")["C"] == "Fe²⁺" and C.key_letter(3) == "C")

# Q4: which test gives different results for Zn2+ and Al3+?
tests = {
    "A": lambda i: CAT[i][1],            # excess NaOH
    "B": lambda i: FLAME.get(i, "none"),  # flame test (neither Al3+ nor Zn2+ colours a flame)
    "C": lambda i: "no change",          # dilute HCl: neither gives a visible difference
    "D": lambda i: "no ppt",             # AgNO3: neither forms a precipitate in the school scheme
    "E": lambda i: CAT[i][3],            # excess NH3
}
diff = [k for k, f in tests.items() if f("Zn2+") != f("Al3+")]
ok(diff == ["E"], diff)
ok(C.options("**4.**")["E"].startswith("adding excess NH₃") and C.key_letter(4) == "E")

# Q5: AgX dissolves in dilute NH3 -> Cl-
ok([x for x, d in dilute.items() if d] == ["Cl-"])
ok(AGX["Cl-"] == "white")
ok(C.options("**5.**")["A"] == "Cl⁻" and C.key_letter(5) == "A")
C.letters_spread()
C.done()
