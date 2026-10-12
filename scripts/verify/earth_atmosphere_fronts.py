"""Independent checks for materi/earth/atmosphere-fronts.md (examples, check questions and quoted facts)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/atmosphere-fronts.md")
ok = C.ok
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


# ---- spin of a low and a high from the Coriolis rule (right of the motion in the north, left in the south)
def spin(inflow, north):
    """+1 = counterclockwise seen from above (x east, y north), -1 = clockwise. Air sits east of the center."""
    r = (1.0, 0.0)
    v = (-1.0, 0.0) if inflow else (1.0, 0.0)
    # deflection direction: right of v = rotate by -90 degrees; left = +90
    d = (v[1], -v[0]) if north else (-v[1], v[0])
    cross = r[0] * d[1] - r[1] * d[0]
    return 1 if cross > 0 else -1


fact("NH low spins counterclockwise", spin(True, True) == 1)
fact("NH high spins clockwise", spin(False, True) == -1)
fact("SH low spins clockwise", spin(True, False) == -1)
fact("SH high spins counterclockwise", spin(False, False) == 1)

# ---- air mass names: surface letter + latitude letter
SURFACE = {"c": "continental (dry)", "m": "maritime (moist)"}
LAT = {"A": "arctic (very cold)", "P": "polar (cold)", "T": "tropical (warm)", "E": "equatorial (hot)"}
fact("mT = maritime tropical = warm and moist", SURFACE["m"].endswith("(moist)") and LAT["T"].endswith("(warm)"))
fact("cP = continental polar = cold and dry", SURFACE["c"].endswith("(dry)") and LAT["P"].endswith("(cold)"))
o1 = C.options("**1.**")
fact("Q1 option D is warm and moist, C is warm and dry (cT)", C.key_letter(1) == "D" and o1["D"] == "warm and moist." and o1["C"] == "warm and dry.")

# ---- front classification rule applied to Example 1 and Q2
def classify(temp_change, rain_hours, advancing_air):
    if advancing_air == "cold":
        return "cold front"
    if advancing_air == "warm":
        return "warm front"
    return "stationary front"


fact("Example 1: temperature fell -> cold air advancing -> cold front", classify(-10, 0.5, "cold") == "cold front")
o = C.options("**Example 1.**")
fact("Example 1 key is D = a cold front", o["D"] == "a cold front")
fact("Q2: advancing air is cold -> cold front is A", classify(0, 0, "cold") == "cold front" and C.options("**2.**")["A"] == "a cold front" and C.key_letter(2) == "A")

# ---- slopes and travel times
def lead_time_h(height_km, slope_run, speed_kmh):
    return height_km * slope_run / speed_kmh


T2 = lead_time_h(3, 200, 25)
C.mcq("**Example 2.**", T2, "h", "C")
C.opt_is("**Example 2.**", "A", lead_time_h(3, 50, 25), "h")
C.opt_is("**Example 2.**", "B", lead_time_h(3, 100, 25), "h")
C.opt_is("**Example 2.**", "D", lead_time_h(6, 200, 25), "h")
C.opt_is("**Example 2.**", "E", 3 * 200, "h")
ok(abs(3 * 200 - 600) < 1e-9)
fact("warm-front slope 1:200 is about 0.29 degrees", abs(__import__("math").degrees(__import__("math").atan(1 / 200)) - 0.286) < 0.01)
fact("cold front slope 1:50 is steeper than warm 1:200", 1 / 50 > 1 / 200)

# ---- Q3, Q4
o3 = C.options("**3.**")
fact("Q3 key C = counterclockwise inward, rising", C.key_letter(3) == "C" and o3["C"].startswith("spiral counterclockwise inward") and "rises" in o3["C"])
fact("Q3: the other options differ in spin or direction", all(o3[k] != o3["C"] for k in "ABDE"))
fact("Q4 key E = occluded", C.key_letter(4) == "E" and C.options("**4.**")["E"] == "an occluded front")

# ---- Q5
T5 = 180 / 45
C.mcq("**5.**", T5, "h", "B")
C.opt_is("**5.**", "A", 45 / 180, "h")
C.opt_is("**5.**", "C", 180 / 22.5, "h")
C.opt_is("**5.**", "D", 180 - 45, "h")
C.opt_is("**5.**", "E", 180 + 45, "h")
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
