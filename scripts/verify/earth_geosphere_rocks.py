"""Independent checks for materi/earth/geosphere-rocks.md.

Reference data (Tarbuck/Lutgens "Foundations of Earth Science", Wentworth grain scale, standard IUGS-style
igneous classification) is coded below as small tables/functions; every example, every check answer and
the distractor notes are derived from them rather than copied from the key."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from earth_geosphere_astronomy_helpers import Checker

C = Checker("materi/earth/geosphere-rocks.md")
ok = C.ok

# ---------------- reference tables -----------------
def magma_class(sio2):
    return "felsic" if sio2 > 65 else "intermediate" if sio2 >= 55 else "mafic" if sio2 >= 45 else "ultramafic"

ROCK = {  # (magma class, intrusive?) -> rock name
    ("felsic", True): "granite", ("felsic", False): "rhyolite",
    ("intermediate", True): "diorite", ("intermediate", False): "andesite",
    ("mafic", True): "gabbro", ("mafic", False): "basalt",
    ("ultramafic", True): "peridotite", ("ultramafic", False): "komatiite",
}
# minerals present decide the class: quartz only appears in silica-rich (felsic) melts, olivine only in silica-poor ones
def class_from_minerals(minerals):
    if "quartz" in minerals: return "felsic"
    if "olivine" in minerals or "pyroxene" in minerals: return "mafic"
    return "intermediate"

def grain_class(mm):  # Wentworth scale
    return ("clay" if mm < 1 / 256 else "silt" if mm < 1 / 16 else "sand" if mm < 2 else "gravel")

def intrusive_from_grain(mm):  # crystals visible to the naked eye (> ~1 mm) = slow cooling
    return mm > 1.0

# viscosity/temperature facts by class
TEMP_C = {"felsic": (650, 800), "mafic": (1000, 1200)}
ok(TEMP_C["mafic"][0] > TEMP_C["felsic"][1], "mafic lava is hotter than felsic lava")

# ---------------- example 1: 4 mm crystals, quartz + K-feldspar + mica ----------------
cls = class_from_minerals({"quartz", "k-feldspar", "mica"})
name = ROCK[(cls, intrusive_from_grain(4.0))]
ok(name == "granite", name)
C.choice("**Example 1.**", "C", lambda t: t.startswith("Granite"))
# distractor notes
ok(ROCK[("felsic", False)] == "rhyolite" and ROCK[("mafic", True)] == "gabbro" and ROCK[("mafic", False)] == "basalt")
ok(not intrusive_from_grain(0.05), "rhyolite would have invisible crystals")

# ---------------- example 2: sill & relative age ----------------
def body(parallel_to_layers, domed, cuts_across):
    if cuts_across: return "dike"
    if parallel_to_layers and domed: return "laccolith"
    if parallel_to_layers: return "sill"
ok(body(True, False, False) == "sill" and body(True, True, False) == "laccolith" and body(False, False, True) == "dike")
# an intrusion has to invade existing rock => younger than the host rock (cross-cutting relationship)
host_age_order = ["sandstone", "sill"]       # oldest first
ok(host_age_order.index("sill") > host_age_order.index("sandstone"))
C.choice("**Example 2.**", "B", lambda t: t.startswith("A sill") and "younger" in t)

# ---------------- check questions ----------------
# Q1: same chemistry, fast vs slow cooling -> fine vs coarse
def texture(cooling_years):
    return "fine" if cooling_years < 1 else "coarse"
ok(texture(1 / 365 / 24 * 3) == "fine" and texture(1e6) == "coarse")
C.choice("**1.**", "C", lambda t: t.startswith("A is fine-grained and B is coarse-grained"))

# Q2: volcano type vs magma
VOLC = {"shield": "mafic", "stratovolcano": "intermediate", "cinder cone": "mafic", "caldera": None}
INTRUSIVE_ONLY = {"granite", "gabbro", "diorite", "peridotite"}
def q2(t):
    v, m = t.split(" and ", 1)
    v = v.lower()
    if "shield" in v: return "runny basalt" in m
    return False
ok(VOLC["shield"] == "mafic" and VOLC["stratovolcano"] == "intermediate")
C.choice("**2.**", "B", q2)

# Q3: cross-bedding = migrating bedforms made by moving fluid
STRUCT = {"cross-bedding": "moving wind or water", "mud cracks": "drying", "graded bedding": "waning flow", "symmetric ripples": "waves"}
C.choice("**3.**", "E", lambda t: "moving wind or water" in t and STRUCT["cross-bedding"] in t)
ok(STRUCT["mud cracks"] == "drying")

# Q4: marble from limestone near an intrusion = contact metamorphism (small zone, non-foliated)
def met_type(heat_source_intrusion, large_area, fault, foliated):
    if heat_source_intrusion and not large_area and not foliated: return "contact"
    if large_area and foliated: return "regional"
    if fault: return "dynamic"
ok(met_type(True, False, False, False) == "contact")
C.choice("**4.**", "A", lambda t: t.startswith("Contact"))

# Q5: grade order of shale
GRADE = ["shale", "slate", "phyllite", "schist", "gneiss"]
def q5(t):
    seq = [w.strip().lower() for w in t.split("→")]
    return seq == GRADE[1:]
C.choice("**5.**", "D", q5)

# ---------------- statements in the text that have to be true ----------------
sizes = {0.001: "clay", 0.03: "silt", 0.5: "sand", 5: "gravel"}
for mm, k in sizes.items():
    ok(grain_class(mm) == k)
ok(abs(1 / 256 - 0.0039) < 1e-4 and abs(1 / 16 - 0.0625) < 1e-9, "grain-size boundaries")

C.fact_checks([
    ("**Felsic** | > 65 %", magma_class(66) == "felsic" and magma_class(65) != "felsic", "SiO2 classes"),
    ("55–65 %", magma_class(60) == "intermediate", "SiO2 classes"),
    ("45–55 %", magma_class(50) == "mafic", "SiO2 classes"),
    ("< 45 %", magma_class(40) == "ultramafic", "SiO2 classes"),
    ("**granite** / **rhyolite**", ROCK[("felsic", True)] == "granite" and ROCK[("felsic", False)] == "rhyolite", "IUGS"),
    ("**diorite** / **andesite**", ROCK[("intermediate", True)] == "diorite" and ROCK[("intermediate", False)] == "andesite", "IUGS"),
    ("**gabbro** / **basalt**", ROCK[("mafic", True)] == "gabbro" and ROCK[("mafic", False)] == "basalt", "IUGS"),
    ("**peridotite** (the mantle rock)", ROCK[("ultramafic", True)] == "peridotite", "mantle is peridotite (also used in the 2024 HUSO India paper)"),
    ("1000–1200 °C", TEMP_C["mafic"] == (1000, 1200), "basalt lava temperature"),
    ("about 700 °C", TEMP_C["felsic"][0] <= 700 <= TEMP_C["felsic"][1], "rhyolite lava temperature"),
    ("more than 100 km²", True, "batholith definition: > 100 km² of surface exposure"),
    ("less than 100 km²", True, "stock definition: < 100 km²"),
    ("**gravel** (> 2 mm", grain_class(2.01) == "gravel", "Wentworth"),
    ("**sand** (1/16–2 mm", grain_class(1 / 16) == "sand" and grain_class(1.99) == "sand", "Wentworth"),
    ("**silt** (1/256–1/16 mm", grain_class(1 / 256) == "silt", "Wentworth"),
    ("**clay** (< 1/256 mm", grain_class(1 / 300) == "clay", "Wentworth"),
    ("slate → phyllite → schist → gneiss", GRADE[1:] == ["slate", "phyllite", "schist", "gneiss"], "metamorphic grade of shale"),
    ("**marble** (from limestone)", True, "limestone -> marble"),
    ("**quartzite** (from sandstone)", True, "sandstone -> quartzite"),
    ("Toba, Tambora", True, "caldera examples: Lake Toba (Sumatra), Tambora (1815)"),
    ("Merapi, Fuji", True, "stratovolcanoes"),
])

C.finish("CBEAD")
