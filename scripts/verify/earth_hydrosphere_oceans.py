"""Independent checks for materi/earth/hydrosphere-oceans.md (tsunami timing, salinity by mass balance, wave speed, tides, heat capacity)."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/hydrosphere-oceans.md")
ok = C.ok
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


G = 9.8
# ---- Example 1: tsunami travel time by stepping along the path (1 km steps), depth constant
depth, dist_km = 4000.0, 1800
c = math.sqrt(G * depth)
t_s = sum(1000.0 / c for _ in range(dist_km))
fact("Example 1: speed 198 m/s = 713 km/h", abs(c - 198.0) < 0.1 and abs(c * 3.6 - 713) < 1)
fact("Example 1: time 9090 s = 2.5 h", abs(t_s - 9090) < 10 and abs(t_s / 3600 - 2.525) < 0.01)
C.mcq("**Example 1.**", t_s / 3600, "h", "D", tol=0.02)
C.opt_is("**Example 1.**", "C", dist_km / c, "h", tol=0.01)                                  # km / (m/s) read as h
C.opt_is("**Example 1.**", "E", 1.8e6 / math.sqrt(depth) / 3600, "h", tol=0.01)              # no g
C.opt_is("**Example 1.**", "B", 1.8e6 / math.sqrt(G * 4) / 3600, "h", tol=0.01)              # depth in km
C.opt_is("**Example 1.**", "A", t_s / 60, "h", tol=0.01)                                      # minutes read as hours
fact("tsunami in the open ocean over 700 km/h at 4000 m", c * 3.6 > 700)
fact("a 100 km wavelength is much longer than 4000 m depth: shallow-water wave", 100e3 / depth > 20)
fact("tsunami at 10 m depth is slow (about 36 km/h)", abs(math.sqrt(G * 10) * 3.6 - 35.6) < 0.5)

# ---- Example 2: salinity by mass balance (simulate boiling in 1 g steps)
water, salt = 965.0, 35.0
removed = 0.0
while removed < 500:
    water -= 1.0
    removed += 1.0
sal = salt / (water + salt) * 1000
fact("Example 2: 500 g left, 35 g salt, 70 g/kg", abs(water + salt - 500) < 1e-9 and abs(sal - 70) < 1e-9)
C.mcq("**Example 2.**", sal, "g/kg", "D")
C.opt_is("**Example 2.**", "B", 35, "g/kg")
C.opt_is("**Example 2.**", "A", 17.5, "g/kg")
C.opt_is("**Example 2.**", "C", 35 + 17.5, "g/kg")
C.opt_is("**Example 2.**", "E", 140, "g/kg")
fact("35 g of salt is about 2 tablespoons (about 17-18 g each)", 1.9 < 35 / 17.7 < 2.1)

# ---- Q2: wave speed, and consistency with deep-water relation L = g T^2 / (2 pi)
v2 = 100 / 8
C.mcq("**2.**", v2, "m/s", "A")
C.opt_is("**2.**", "B", 8 / 100, "m/s", tol=0.01)
C.opt_is("**2.**", "C", 800, "m/s")
C.opt_is("**2.**", "D", 108, "m/s")
C.opt_is("**2.**", "E", 100 / 16, "m/s")
fact("Q2 data are a consistent deep-water wave (L = 1.56 T^2 = 100 m for T = 8 s)", abs(9.81 * 8 ** 2 / (2 * math.pi) - 100) < 1)
fact("deep water speed c = 1.56 T = 12.5 m/s", abs(9.81 * 8 / (2 * math.pi) - 12.5) < 0.1)

# ---- tides
lunar_day_h = 24 + 50.47 / 60       # a lunar (tidal) day: 24 h 50 min
fact("two high tides per lunar day are 12 h 25 min apart", abs(lunar_day_h / 2 - (12 + 25 / 60)) < 0.01)
SYN = 29.53
fact("spring-neap cycle is about 14.8 days (half a synodic month)", abs(SYN / 2 - 14.8) < 0.05)
fact("tides are about 50 min later each day", abs((24.8412 - 24) * 60 - 50.5) < 0.5)
def tide_range_factor(phase_deg):   # relative size of the combined Sun+Moon tide (Moon 1.0, Sun 0.46)
    return math.sqrt(1 + 0.46 ** 2 + 2 * 0.46 * math.cos(math.radians(2 * phase_deg)))
fact("range is largest at new/full moon (phase 0, 180) and smallest at quarters (90, 270)",
     tide_range_factor(0) > tide_range_factor(45) > tide_range_factor(90) and abs(tide_range_factor(0) - tide_range_factor(180)) < 1e-9)
o3 = C.options("**3.**")
fact("Q3 key E = line up", C.key_letter(3) == "E" and o3["E"] == "the Sun, Earth and Moon are in a line.")

# ---- heat capacity: top 3-4 m of the ocean ~ whole atmosphere
M_ATM, CP_AIR = 5.148e18, 1004.0
AREA_OCEAN, RHO_SW, CP_SW = 3.61e14, 1025.0, 3990.0
depth_equiv = M_ATM * CP_AIR / (AREA_OCEAN * RHO_SW * CP_SW)
fact("top 3 to 4 m of ocean = heat capacity of the atmosphere", 3.0 <= depth_equiv <= 4.0)

# ---- salinity facts
IONS = {"Cl": 55.0, "Na": 30.6, "SO4": 7.7, "Mg": 3.7, "Ca": 1.2, "K": 1.1}
fact("main ions sum to about 99 % of the salt; Cl about 55 and Na about 31", 99 <= sum(IONS.values()) <= 100 and round(IONS["Na"]) == 31)
S = 35.0
tf = -0.0575 * S + 1.710523e-3 * S ** 1.5 - 2.154996e-4 * S ** 2
fact("seawater (35 per mille) freezes at about -1.9 C", abs(tf - (-1.9)) < 0.05)

# ---- gyre direction from wind-stress curl logic: Ekman transport 90 degrees to the right of the wind (north)
def ekman(wind_to, north):
    return (wind_to[1], -wind_to[0]) if north else (-wind_to[1], wind_to[0])
westerly, trade = (1, 0), (-1, 0)             # wind blowing toward east / toward west
# at 45 N the westerlies push water net toward the SOUTH (right of east); at 15 N the trades push net NORTH (right of west)
fact("NH Ekman: westerlies move water south, trades move water north, so water piles in the middle at 30 N",
     ekman(westerly, True) == (0, -1) and ekman(trade, True) == (0, 1))
fact("SH Ekman is the mirror image", ekman(westerly, False) == (0, 1) and ekman(trade, False) == (0, -1))
# gyre flow: east along the north edge, south on the east, west along the south, north on the west: clockwise in the NH
pts = [(0, 1), (1, 0), (0, -1), (-1, 0)]       # positions N, E, S, W; flows (east, south, west, north)
flows = [(1, 0), (0, -1), (-1, 0), (0, 1)]
spin = sum(p[0] * f[1] - p[1] * f[0] for p, f in zip(pts, flows))
fact("flows east on top, south on the right ... = clockwise (negative cross product)", spin < 0)

# ---- Q1, Q4, Q5
o1 = C.options("**1.**")
fact("Q1 key C = narrow, fast, warm toward the poles", C.key_letter(1) == "C" and "narrow, fast" in o1["C"] and "toward the poles" in o1["C"])
o4 = C.options("**4.**")
fact("Q4 key B", C.key_letter(4) == "B" and "very cold and salty" in o4["B"])
o5 = C.options("**5.**")
fact("Q5 key D = cave, arch, stack, stump; the file lists crack as stage zero", C.key_letter(5) == "D" and o5["D"] == "cave → arch → stack → stump" and "crack → cave → arch → stack → stump" in C.txt)
fact("carbonate compensation depth quoted 4 to 5 km", "4 to 5 km" in C.txt)
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
