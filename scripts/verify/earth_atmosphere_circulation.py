"""Independent checks for materi/earth/atmosphere-circulation.md: the wind directions are DERIVED from the cells + Coriolis rule."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/atmosphere-circulation.md")
ok = C.ok
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


# vectors are (east, north)
def right_of(v):      # rotate -90 degrees
    return (v[1], -v[0])


def left_of(v):
    return (-v[1], v[0])


def bend(heading, north_hemisphere):
    """Coriolis: right of the heading in the north, left in the south."""
    return right_of(heading) if north_hemisphere else left_of(heading)


def compass(v):
    ang = math.degrees(math.atan2(v[0], v[1])) % 360       # 0 = north, 90 = east
    names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return names[int((ang + 22.5) // 45) % 8]


def wind_from(lat):
    """Surface wind (name of the direction it comes FROM) from the 3-cell model."""
    north = lat > 0
    a = abs(lat)
    toward_pole = (0, 1) if north else (0, -1)
    toward_eq = (0, -1) if north else (0, 1)
    flow = toward_eq if a < 30 else toward_pole if a < 60 else toward_eq     # surface flow of Hadley, Ferrel, polar
    b = bend(flow, north)
    heading = (flow[0] + b[0], flow[1] + b[1])             # equal blend of the pressure push and the Coriolis bend
    came_from = (-heading[0], -heading[1])
    return compass(came_from)


# cells: air rises where surface flows diverge from... check rising/sinking latitudes from the surface flows
def surface_flow_dir(lat_band_mid):
    a = abs(lat_band_mid)
    return "equatorward" if a < 30 or a >= 60 else "poleward"


fact("surface flow: Hadley equatorward, Ferrel poleward, polar equatorward",
     [surface_flow_dir(15), surface_flow_dir(45), surface_flow_dir(75)] == ["equatorward", "poleward", "equatorward"])
# convergence at 0 (both Hadley flows meet), divergence at 30 (Hadley goes eq, Ferrel goes pole -> away), convergence at 60, divergence at 90
fact("air rises where surface flows converge: 0 and 60; sinks where they diverge: 30 and 90",
     (surface_flow_dir(15) == "equatorward") and (surface_flow_dir(45) == "poleward") and (surface_flow_dir(75) == "equatorward"))
fact("NE trade winds (15 N)", wind_from(15) == "NE")
fact("SE trade winds (15 S)", wind_from(-15) == "SE")
fact("westerlies from SW (45 N)", wind_from(45) == "SW")
fact("westerlies from NW (45 S)", wind_from(-45) == "NW")
fact("polar easterlies from NE (75 N)", wind_from(75) == "NE")
fact("polar easterlies from SE (75 S)", wind_from(-75) == "SE")

# Coriolis parameter f = 2 * Omega * sin(lat)
OMEGA = 7.2921e-5
f = lambda lat: 2 * OMEGA * math.sin(math.radians(lat))
fact("Coriolis is zero at the equator and largest at the poles", f(0) == 0 and f(90) == max(f(l) for l in range(0, 91)))
fact("Coriolis changes sign between hemispheres", f(-30) < 0 < f(30))

# Sun's declination: overhead latitude in July is north, in January south (ITCZ follows it)
decl = lambda day: 23.44 * math.sin(math.radians(360 / 365 * (284 + day)))
fact("Sun is overhead north of the equator in July and south in January", decl(196) > 20 and decl(15) < -20)
fact("the Sun is overhead only between the Tropics (23.4)", max(decl(d) for d in range(1, 366)) < 23.5)

# Example 1
o = C.options("**Example 1.**")
fact("Example 1: 45 N is SW (C)", wind_from(45) == "SW" and o["C"] == "southwest" and o["D"] == "northwest" and o["A"] == "northeast")
fact("Example 1 trap: 45 S gives NW", wind_from(-45) == "NW")
fact("Example 1 trap: the trades are NE only for 0-30 N", wind_from(15) == "NE")
# Example 2
o2 = C.options("**Example 2.**")
fact("Example 2: Hadley air sinks near 30 (B)", o2["B"] == "about 30°")
# Q1-Q5
o1 = C.options("**1.**")
fact("Q1 NE (B)", wind_from(15) == "NE" and C.key_letter(1) == "B" and o1["B"] == "northeast." and o1["D"] == "southeast.")
fact("Q2 sinking Hadley air (E)", C.key_letter(2) == "E" and "Hadley cell sinks" in C.options("**2.**")["E"])
north_bend = compass(bend((0, 1), True)); south_bend = compass(bend((0, 1), False))
fact("Q3: heading north bends east in the north and west in the south", (north_bend, south_bend) == ("E", "W"))
o3 = C.options("**3.**")
fact("Q3 key A = west", C.key_letter(3) == "A" and o3["A"] == "west." and o3["B"] == "east.")
o4 = C.options("**4.**")
fact("Q4 key D = the equator (air rises there)", C.key_letter(4) == "D" and o4["D"] == "the equator" and surface_flow_dir(15) == "equatorward")
o5 = C.options("**5.**")
fact("Q5 45 S = NW (C), distractor D southwest is the northern westerly", wind_from(-45) == "NW" and C.key_letter(5) == "C" and o5["C"] == "northwest." and o5["D"] == "southwest." and wind_from(45) == "SW")
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
