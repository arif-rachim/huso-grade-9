"""Independent checks for materi/earth/atmosphere-phenomena.md (foehn simulation, Saffir-Simpson, thunder timing, sea breeze, ENSO)."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/atmosphere-phenomena.md")
ok = C.ok
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


# ---- Saffir-Simpson: category from sustained wind (thresholds in mph are the official ones; km/h by conversion)
MPH = 1.609344
CATS_MPH = [(74, 1), (96, 2), (111, 3), (130, 4), (157, 5)]


def category(kmh):
    c = 0
    for lo, k in CATS_MPH:
        if kmh >= int(lo * MPH):
            c = k
    return c


lows = [int(lo * MPH) for lo, _ in CATS_MPH]
fact("km/h thresholds 119, 154, 178, 209, 252 as in the file", lows == [119, 154, 178, 209, 252])
for s in ("119 to 153", "154 to 177", "178 to 208", "209 to 251", "252 km/h or more"):
    fact(f"file prints '{s}'", s in C.txt)
fact("each upper bound is the next lower bound minus 1", [lows[i + 1] - 1 for i in range(4)] == [153, 177, 208, 251])
v = 60 * 3.6
fact("Example 1: 60 m/s = 216 km/h", abs(v - 216) < 1e-9)
fact("Example 1: category 4", category(v) == 4)
o = C.options("**Example 1.**")
fact("Example 1 key text is Category 4 (D)", o["D"] == "Category 4" and len(o) == 5)
fact("Example 1 trap: 60 km/h is not a hurricane", category(60) == 0)
fact("hurricane minimum 74 mph = 119 km/h", int(74 * MPH) == 119)

# ---- Example 2: foehn by stepping through the mountain in 1 m steps
t = 20.0
z = 0.0
cloud_at = 1000.0
while z < 3000:
    t -= (10 if z < cloud_at else 5) / 1000
    z += 1
summit = t
fact("Example 2: summit is 0 C", abs(summit - 0) < 1e-6)
temp_at_cloud = 20 - 10 * 1.0
fact("Example 2: 10 C at the cloud base", temp_at_cloud == 10)
down = summit + 10 * 3.0
fact("Example 2: 30 C at the bottom", abs(down - 30) < 1e-6)
C.mcq("**Example 2.**", down, "°C", "D")
C.opt_is("**Example 2.**", "B", 20 - 10 * 3 + 10 * 3, "°C")           # dry rate both ways
C.opt_is("**Example 2.**", "A", summit + 5 * 3, "°C")                 # moist rate on the way down
C.opt_is("**Example 2.**", "C", temp_at_cloud, "°C")
C.opt_is("**Example 2.**", "E", summit, "°C")
fact("foehn air ends warmer than it began", down > 20)

# ---- speed of sound and thunder
c_sound = 331.3 + 0.606 * 20
fact("speed of sound at 20 C is about 343 m/s", abs(c_sound - 343) < 0.6)
d5 = 343 * 9
C.mcq("**5.**", d5, "m", "C", tol=0.05)
fact("Q5: 3087 m is about 3 km; seconds / 3 rule gives 3", abs(d5 / 1000 - 3.087) < 1e-9 and 9 / 3 == 3)
C.opt_is("**5.**", "D", 9000, "m")
C.opt_is("**5.**", "E", 27000, "m")
fact("Q5 options A and B are not 3 km", C.options("**5.**")["A"] == "1 km" and C.options("**5.**")["B"] == "2 km")
fact("lightning about 30 000 C is about 5 times the Sun's surface (5772 K)", 5 < 30000 / 5772 < 5.5)

# ---- sea breeze: heat land and sea with the same energy and compare
# land: c = 800 J/(kg K) top 0.1 m layer of soil rho 1500 ; sea: c = 3990, mixed layer 10 m rho 1025
flux = 600.0 * 6 * 3600                                        # 6 h of 600 W/m2 absorbed
dT_land = flux / (800 * 1500 * 0.1)
dT_sea = flux / (3990 * 1025 * 10)
fact("land warms far more than the sea in the same sunshine (sea breeze by day)", dT_land > 50 * dT_sea)
fact("warmer surface -> lower pressure -> wind blows from the sea to the land", (dT_land > dT_sea))
o2 = C.options("**2.**")
fact("Q2 key B = from the sea toward the land", C.key_letter(2) == "B" and o2["B"] == "From the sea toward the land." and o2["A"] == "From the land toward the sea.")

# ---- Q1, Q3, Q4
o1 = C.options("**1.**")
fact("Q1 key D = cumulonimbus; E nimbostratus is the distractor", C.key_letter(1) == "D" and o1["D"] == "cumulonimbus." and o1["E"] == "nimbostratus.")
o3 = C.options("**3.**")
fact("Q3 key A = drier", C.key_letter(3) == "A" and o3["A"].startswith("A drier than normal"))
# ENSO logic: rain over where the warm pool is; warm pool longitude shifts east in El Nino
POOL_LON = {"normal": 130, "el_nino": 180, "la_nina": 120}          # approximate center of the warm pool (deg E)
INDONESIA_LON = 115
fact("distance of the rain from Indonesia grows in El Nino and shrinks in La Nina",
     POOL_LON["el_nino"] - INDONESIA_LON > POOL_LON["normal"] - INDONESIA_LON > POOL_LON["la_nina"] - INDONESIA_LON)
f = lambda lat: 2 * 7.2921e-5 * math.sin(math.radians(lat))
fact("Coriolis is zero at the equator and tiny at 2 degrees compared with 15", f(0) == 0 and f(2) < 0.15 * f(15))
fact("5 degrees is only ~1/3 of the value at 15 degrees", f(5) / f(15) < 0.35)
o4 = C.options("**4.**")
fact("Q4 key E = Coriolis", C.key_letter(4) == "E" and "Coriolis" in o4["E"] and all("Coriolis" not in o4[k] for k in "ABCD"))
fact("monsoon rainy season in Indonesia is Nov-Mar and in South Asia Jun-Sep (as written)", "northwest monsoon (about November to March)" in C.txt and "(June to September)" in C.txt)
fact("ocean temperature threshold 26.5 C is in the file", "26.5 °C" in C.txt)
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
