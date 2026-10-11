"""Independent checks for materi/earth/geosphere-interior.md.

Numbers (S-P distance) are recomputed by simulating wave arrival times; concept questions use small
reference tables (PREM-style layer depths, fault geometry, soil horizons) coded below."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from earth_geosphere_astronomy_helpers import Checker

C = Checker("materi/earth/geosphere-interior.md")
ok = C.ok

# ---------------- reference: layers (PREM boundaries) -----------------
R_EARTH = 6371.0
LAYERS = [  # (name, top depth km, bottom depth km, state, composition)
    ("crust", 0, 35, "solid", "silicate rock"),
    ("mantle", 35, 2890, "solid", "peridotite"),
    ("outer core", 2890, 5150, "liquid", "iron-nickel"),
    ("inner core", 5150, 6371, "solid", "iron-nickel"),
]
def layer_at(depth):
    return next(l for l in LAYERS if l[1] <= depth < l[2] or (depth == 6371 and l[0] == "inner core"))

ok(layer_at(4000)[0] == "outer core" and layer_at(4000)[3] == "liquid")
ok(abs((R_EARTH - 5150) - 1221) < 1, "inner core radius is about 1220 km")
ok(abs((R_EARTH - 2890) - 3481) < 1, "core radius is about 3480 km")
mantle_volume_share = (( (R_EARTH - 35) ** 3 - (R_EARTH - 2890) ** 3) / R_EARTH ** 3)
ok(0.82 < mantle_volume_share < 0.86, mantle_volume_share)       # 'about 84 %'

# ---------------- example 1: S-P time -> distance, by brute-force arrival times ----------------
vP, vS, gap = 6.0, 3.5, 25.0
d = 0.0
while (d / vS - d / vP) < gap:
    d += 0.001
ok(abs(d - 210.0) < 0.01, d)
C.mcq("**Example 1.**", d, "D")
C.opt_is("**Example 1.**", "C", vP * gap)                    # used only the P speed
C.opt_is("**Example 1.**", "B", vS * gap)                    # only the S speed
C.opt_is("**Example 1.**", "A", (vP - vS) * gap)             # multiplied by the speed difference
C.opt_is("**Example 1.**", "E", vP * vS * gap)               # forgot to divide by the difference
ok(abs(vP * vS / (vP - vS) - 8.4) < 1e-12, "8.4 km per second of gap")
ok(abs(1 / vS - 1 / vP - 0.119) < 5e-4, "0.119 s per km")
ok(abs(1 / math.sqrt(3) - 0.577) < 1e-3, "Vs/Vp for a Poisson solid is about 0.6")

# ---------------- example 2: fault geometry -> stress -> boundary ----------------
def fault_type(hanging_wall_moves):       # 'down' / 'up' / 'sideways'
    return {"down": "normal", "up": "reverse", "sideways": "strike-slip"}[hanging_wall_moves]
STRESS = {"normal": "tension", "reverse": "compression", "strike-slip": "shear"}
BOUNDARY = {"normal": "divergent", "reverse": "convergent", "strike-slip": "transform"}
ft = fault_type("down")
want = (STRESS[ft], ft, BOUNDARY[ft])
def parse(t):
    stress, rest = t.split(", ", 1)
    fault, bound = rest.split(", ", 1)
    return stress.lower(), fault.replace(" fault", ""), bound.replace(" boundary", "")
C.choice("**Example 2.**", "B", lambda t: parse(t) == want)

# ---------------- check questions ----------------
# Q1: S waves cannot travel in liquid; they are absent beyond 103 deg => a liquid layer on the path => outer core
PASSES_LIQUID = {"S": False, "P": True}
ok(not PASSES_LIQUID["S"] and PASSES_LIQUID["P"])
C.choice("**1.**", "B", lambda t: "outer core is liquid" in t)

# Q2
C.choice("**2.**", "C", lambda t: t == "Liquid iron and nickel" and layer_at(4000)[3] == "liquid" and layer_at(4000)[4] == "iron-nickel")

# Q3: slanted deep-quake zone under a trench = subduction = convergent
def boundary_from(features):
    if "trench" in features and "dipping deep quakes" in features: return "convergent-subduction"
    if "ridge" in features: return "divergent"
    return "transform"
ok(boundary_from({"trench", "dipping deep quakes"}) == "convergent-subduction")
C.choice("**3.**", "A", lambda t: t.startswith("Convergent"))

# Q4: strike-slip sense by geometry. Fault runs north-south (y axis). Observer stands west (x<0), looks east.
def lateral_sense(look, displacement_of_far_block):
    cross = look[0] * displacement_of_far_block[1] - look[1] * displacement_of_far_block[0]
    return "right-lateral" if cross < 0 else "left-lateral"      # cross < 0: clockwise = to the right
ok(lateral_sense((1, 0), (0, -1)) == "right-lateral")            # looking east, south is to the right
ok(lateral_sense((1, 0), (0, 1)) == "left-lateral")
ok(lateral_sense((-1, 0), (0, 1)) == "right-lateral", "same fault seen from the other side")   # looking west, north is to the right
C.choice("**4.**", "C", lambda t: t == "A right-lateral strike-slip fault")

# Q5: soil horizons
HOR = {"O": "organic litter", "A": "topsoil", "E": "eluviation (leached)", "B": "illuviation (accumulation of clay and iron)",
       "C": "weathered parent material", "R": "bedrock"}
C.choice("**5.**", "D", lambda t: HOR[t].startswith("illuviation"))

# ---------------- facts in the text ----------------
C.fact_checks([
    ("oceanic about 7 km of basalt", True, "oceanic crust 5-10 km (mean ~7 km)"),
    ("continental about 35 km", True, "continental crust 30-50 km"),
    ("to 2890 km", LAYERS[1][2] == 2890, "Gutenberg discontinuity"),
    ("2890 to 5150 km", LAYERS[2][1:3] == (2890, 5150), "PREM"),
    ("5150 to 6371 km", LAYERS[3][1:3] == (5150, 6371), "PREM"),
    ("about 84 % of Earth's volume", 0.82 < mantle_volume_share < 0.86, "computed from the radii"),
    ("0.6 × as fast as P", abs(1 / math.sqrt(3) - 0.6) < 0.03, "Vs/Vp for a Poisson solid = 1/sqrt(3)"),
    ("103° to 142°", True, "P-wave shadow zone (IRIS)"),
    ("32 times more energy", abs(10 ** 1.5 - 31.6) < 0.1, "energy ~ 10^(1.5 M)"),
    ("10 times bigger shaking", True, "amplitude ~ 10^M"),
    ("hanging wall moves **down**", True, "normal fault definition"),
    ("hanging wall moves **up**", True, "reverse fault definition"),
    ("Himalayas", True, "continent-continent collision"),
    ("Sunda arc of Indonesia", True, "Indo-Australian plate subducts beneath the Sunda plate (Eurasian plate)"),
    ("**Mollisols**", True, "USDA soil orders"),
    ("**Oxisols**", True, "USDA soil orders"),
    ("**Gelisols**", True, "USDA soil orders"),
    ("**Histosols**", True, "USDA soil orders"),
    ("**Aridisols**", True, "USDA soil orders"),
    ("**Entisols**", True, "USDA soil orders"),
])

C.finish("BCACD")
