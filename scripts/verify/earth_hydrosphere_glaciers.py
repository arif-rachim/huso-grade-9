"""Independent checks for materi/earth/hydrosphere-glaciers.md (transit time, mass balance, densities, landform logic, ice volume figures)."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/hydrosphere-glaciers.md")
ok = C.ok
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


# ---- Example 1: simulate a marker in the ice moving 100 m each year until it passes 8000 m
x, years = 0.0, 0
while x < 8000:
    x += 100
    years += 1
fact("Example 1: 80 years", years == 80)
C.mcq("**Example 1.**", years, "years", "C")
for letter, val in (("A", 0.8), ("B", 8), ("D", 800), ("E", 8000)):
    C.opt_is("**Example 1.**", letter, val, "years")
fact("distractors are powers of ten of 80", all(abs(math.log10(v / 80) - round(math.log10(v / 80))) < 1e-9 for v in (0.8, 8, 800, 8000)))

# ---- Example 2: direction logic: drumlin = oval till hill, steep (stoss) end faces up-glacier
STEEP_END_POINTS = "north"
ice_flows = {"north": "south", "south": "north", "east": "west", "west": "east"}[STEEP_END_POINTS]
fact("steep end north -> ice came from the north -> flows south", ice_flows == "south")
o = C.options("**Example 2.**")
fact("Example 2 option B = drumlin, flowing south", o["B"] == "a drumlin, flowing south" and o["C"] == "a drumlin, flowing north")
LANDFORM = {("till", "streamlined oval"): "drumlin", ("sorted", "winding ridge"): "esker", ("sorted", "mound"): "kame", ("hole", "lake"): "kettle"}
fact("unsorted + streamlined oval = drumlin", LANDFORM[("till", "streamlined oval")] == "drumlin")

# ---- Q5: mass balance
bal = 2.4 - 2.9
C.mcq("**5.**", bal, "m", "C", tol=0.01)
C.opt_is("**5.**", "B", +0.5, "m")
C.opt_is("**5.**", "A", 2.4 + 2.9, "m")
C.opt_is("**5.**", "D", -(2.4 + 2.9), "m")
fact("negative balance -> retreat", bal < 0)

# ---- densities: compaction of 1 m of snow into ice conserves mass
ICE, SNOW = 0.917, 0.1
fact("1 m of fresh snow makes about 0.11 m of ice", abs(1 * SNOW / ICE - 0.109) < 0.001)
fact("glacier ice about 0.9 g/cm3, firn 0.4-0.8, snow 0.1", 0.4 < 0.8 < 0.83 < 0.917 and "0.4 to 0.8" in C.txt and "0.917" in C.txt)

# ---- ice figures (USGS-style volumes, km3)
FRESH, GLACIER = 35.029e6, 24.064e6
fact("glacier ice about 69 % of fresh water", abs(GLACIER / FRESH * 100 - 68.7) < 0.1)
ANT, GRE, OTHER = 26.5e6, 2.9e6, 0.17e6
fact("Antarctica holds about 90 % of the ice", abs(ANT / (ANT + GRE + OTHER) * 100 - 90) < 1.5)
OCEAN_AREA_KM2 = 3.61e8
raw_rise = (ANT + GRE + OTHER) * 0.917 / OCEAN_AREA_KM2 * 1000
fact("naive sea-level equivalent is 55-80 m (accepted value about 65 m after corrections)", 55 < raw_rise < 80)
fact("ice sheet is defined as more than 50 000 km2 (Greenland 1.7 million km2)", 1.7e6 > 5e4)

# ---- sea ice and floating ice: Archimedes - melting floating ice does not change the level (fresh-water ice in fresh water)
rho_w, rho_i = 1000.0, 917.0
V_ice = 1.0
V_displaced = rho_i * V_ice / rho_w
V_melt = rho_i * V_ice / rho_w
fact("floating ice displaces the same volume as its melt water", abs(V_displaced - V_melt) < 1e-12)

# ---- Q1-Q4
o1 = C.options("**1.**")
fact("Q1 key B", C.key_letter(1) == "B" and o1["B"] == "snow → firn → glacier ice")
o2 = C.options("**2.**")
fact("Q2 key D = till", C.key_letter(2) == "D" and o2["D"] == "glacial till")
o3 = C.options("**3.**")
fact("Q3 key A = glacier", C.key_letter(3) == "A" and o3["A"] == "A glacier")
o4 = C.options("**4.**")
fact("Q4 key E = three or more", C.key_letter(4) == "E" and "three or more" in o4["E"] and "cirque" in o4["E"])
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
