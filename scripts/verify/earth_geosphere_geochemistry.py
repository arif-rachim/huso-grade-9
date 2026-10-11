"""Independent checks for materi/earth/geosphere-geochemistry.md.

The boiling temperature of water at 2 atm is computed from the Antoine equation (a fitted vapor-pressure
curve), not read off the key. Minerals, Bowen assemblages and the Mohs tool scale are reference tables."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from earth_geosphere_astronomy_helpers import Checker

C = Checker("materi/earth/geosphere-geochemistry.md")
ok = C.ok

# ---------------- example 1: pressure cooker ----------------
ATM_MMHG = 760.0
def p_sat_atm(T_c):                       # Antoine, water, 1-100 C constants extended with the 99-374 C set
    if T_c <= 100:
        A, B, Cc = 8.07131, 1730.63, 233.426
    else:
        A, B, Cc = 8.14019, 1810.94, 244.485
    return 10 ** (A - B / (Cc + T_c)) / ATM_MMHG

def t_boil(p_atm):
    lo, hi = 1.0, 300.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if p_sat_atm(mid) < p_atm:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

ok(abs(t_boil(1.0) - 100.0) < 0.3, t_boil(1.0))
T2 = t_boil(2.0)
ok(abs(T2 - 120.2) < 1.0, T2)
C.mcq("**Example 1.**", T2, "C", tol=0.02)
ok(p_sat_atm(80) < 0.5, "80 C boils only at about 0.47 atm: a very high mountain")
ok(3.3 < p_sat_atm(140) < 3.9 and 14 < p_sat_atm(200) < 17, "140 C needs ~3.6 atm, 200 C needs ~15.5 atm")
ok(T2 < 125, "so 2 atm is not 140 C")

# ---------------- example 2: Bowen assemblages ----------------
ASSEMBLAGES = {
    "gabbro/basalt": {"olivine", "pyroxene", "ca-plagioclase"},
    "diorite/andesite": {"amphibole", "plagioclase", "biotite", "pyroxene"},
    "granite/rhyolite": {"quartz", "k-feldspar", "na-plagioclase", "muscovite", "biotite"},
}
def possible(minerals):
    return any(set(minerals) <= a for a in ASSEMBLAGES.values())
CHOICES = {"A": {"olivine", "quartz"}, "B": {"quartz", "k-feldspar", "muscovite"}, "C": {"olivine", "k-feldspar"},
           "D": {"ca-plagioclase", "quartz"}, "E": {"pyroxene", "muscovite"}}
ok([k for k, v in CHOICES.items() if possible(v)] == ["B"])
def ex2(t):
    t = t.lower()
    keys = [("olivine", "olivine"), ("quartz", "quartz"), ("k-feldspar", "k-feldspar"), ("ca-rich plagioclase", "ca-plagioclase"),
            ("pyroxene", "pyroxene"), ("muscovite", "muscovite")]
    return possible({v for k, v in keys if k in t})
C.choice("**Example 2.**", "B", ex2)

# ---------------- Q1: eutectic of salt water ----------------
EUTECTIC_NACL_C = -21.1                      # at 23.3 % NaCl by mass
ok(-21.5 < EUTECTIC_NACL_C < -20.5 and EUTECTIC_NACL_C < -18 < 0)
C.choice("**1.**", "D", lambda t: "lowers the melting point" in t and "below 0 °C" in t)

# ---------------- Q2: Mohs tools ----------------
TOOLS = {"fingernail": 2.5, "copper coin": 3.5, "steel knife": 5.5, "steel file": 6.5}
lo, hi = TOOLS["copper coin"], TOOLS["steel knife"]       # not scratched by 3.5 -> H >= 3.5 ; scratched by 5.5 -> H < 5.5
ok((lo, hi) == (3.5, 5.5))
RANGES = {"A": (0, 2.5), "B": (2.5, 3.5), "C": (3.5, 5.5), "D": (5.5, 6.5), "E": (6.5, 10)}
ok([k for k, r in RANGES.items() if r[0] >= lo and r[1] <= hi] == ["C"])
def q2(t):
    return t == "between 3.5 and 5.5"
C.choice("**2.**", "C", q2)

# ---------------- Q3: Bowen ----------------
KIND = {"quartz": "felsic", "k-feldspar": "felsic", "muscovite": "felsic", "olivine": "mafic", "pyroxene": "mafic", "ca-plagioclase": "mafic"}
rock = {KIND[m] for m in ("quartz", "k-feldspar", "muscovite")}
ok(rock == {"felsic"})
WEATHERING_RANK = ["olivine", "pyroxene", "amphibole", "biotite", "k-feldspar", "muscovite", "quartz"]  # fastest -> slowest (Goldich)
ok(WEATHERING_RANK.index("olivine") < WEATHERING_RANK.index("quartz"))
C.choice("**3.**", "A", lambda t: t.startswith("A felsic rock that crystallized from a cool, silica-rich magma"))

# ---------------- Q4: mineral identification ----------------
MIN = {
    "halite": dict(cleav=3, right_angle=True, fizz=False), "calcite": dict(cleav=3, right_angle=False, fizz=True),
    "quartz": dict(cleav=0, right_angle=None, fizz=False), "mica": dict(cleav=1, right_angle=None, fizz=False),
    "pyroxene": dict(cleav=2, right_angle=True, fizz=False),
}
match = [m for m, d in MIN.items() if d["cleav"] == 3 and d["right_angle"] is False and d["fizz"]]
ok(match == ["calcite"])
C.choice("**4.**", "B", lambda t: t == "Calcite")

# ---------------- Q5: water below its triple point ----------------
P_TRIPLE_ATM = 611.657 / 101325
P_CRIT_ATM = 22.064e6 / 101325
ok(abs(P_TRIPLE_ATM - 0.00604) < 1e-5 and abs(P_CRIT_ATM - 217.7) < 0.2)
def phases_met(p_atm):
    seen = []
    for T in range(-100, 700):
        if p_atm < P_TRIPLE_ATM:
            ph = "solid" if T < -60 + 40 * math.log10(p_atm / 0.0001) else "vapor"   # sublimation line (schematic)
        elif p_atm > P_CRIT_ATM:
            ph = "solid" if T < 0 else "supercritical" if T > 374 else "liquid"
        else:
            ph = "solid" if T < 0 else "liquid" if T < t_boil(p_atm) else "vapor"
        if not seen or seen[-1] != ph:
            seen.append(ph)
    return seen
ok(phases_met(0.001) == ["solid", "vapor"], phases_met(0.001))
ok("liquid" in phases_met(1.0) and "liquid" not in phases_met(0.001))
C.choice("**5.**", "E", lambda t: t == "It turns directly into water vapor")

# ---------------- facts in the text ----------------
CRUST = {"O": 46.6, "Si": 27.7, "Al": 8.1, "Fe": 5.0, "Ca": 3.6, "Na": 2.8, "K": 2.6, "Mg": 2.1}
ok(abs(sum(CRUST.values()) - 98.5) < 1e-9)
MOHS = ["talc", "gypsum", "calcite", "fluorite", "apatite", "orthoclase", "quartz", "topaz", "corundum", "diamond"]
ok(len(MOHS) == 10 and MOHS[6] == "quartz" and MOHS[2] == "calcite")
C.fact_checks([
    ("**O 46.6 %, Si 27.7 %, Al 8.1 %, Fe 5.0 %, Ca 3.6 %, Na 2.8 %, K 2.6 %, Mg 2.1 %**", CRUST["O"] == 46.6 and CRUST["Mg"] == 2.1, "Tarbuck: abundance of elements in the crust"),
    ("98.5 %", abs(sum(CRUST.values()) - 98.5) < 1e-9, "sum of the eight"),
    ("(talc, gypsum, calcite, fluorite, apatite, orthoclase, quartz, topaz, corundum, diamond)", ", ".join(MOHS) == "talc, gypsum, calcite, fluorite, apatite, orthoclase, quartz, topaz, corundum, diamond", "Mohs scale"),
    ("fingernail 2.5, copper coin 3.5, steel knife or glass 5.5, steel file 6.5", TOOLS["fingernail"] == 2.5 and TOOLS["steel file"] == 6.5, "standard hardness tools"),
    ("**triple point** (0.01 °C, 0.006 atm)", abs(P_TRIPLE_ATM - 0.006) < 1e-4, "water triple point 273.16 K, 611.657 Pa"),
    ("**critical point** (374 °C, 218 atm)", abs(P_CRIT_ATM - 218) < 1, "water critical point 647.1 K, 22.064 MPa"),
    ("Salt + water has a eutectic at −21 °C", abs(EUTECTIC_NACL_C + 21) < 0.5, "NaCl-water eutectic -21.1 C"),
    ("2 directions at about 90° (87°)", True, "pyroxene cleavage 87/93 degrees"),
    ("2 directions at 56° and 124°", True, "amphibole cleavage 56/124 degrees"),
    ("3 directions at 90° (cubes)", True, "halite cubic cleavage"),
    ("3 directions, not at 90° (rhombs)", True, "calcite rhombohedral cleavage 75/105"),
    ("six-sided prisms", True, "quartz habit (hexagonal prisms)"),
    ("olivine and quartz do not occur together", ASSEMBLAGES and not possible({"olivine", "quartz"}), "Bowen: olivine reacts with silica-rich melt"),
    ("olivine fastest, quartz slowest", WEATHERING_RANK[0] == "olivine" and WEATHERING_RANK[-1] == "quartz", "Goldich weathering series"),
    ("olivine → pyroxene → amphibole → biotite", True, "Bowen discontinuous series"),
    ("**K-feldspar → muscovite → quartz**", True, "Bowen final stage"),
    ("hematite is reddish-brown in streak", True, "hematite streak"),
])

C.finish("DCABE")
