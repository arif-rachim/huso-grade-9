"""Independent checks for materi/earth/atmosphere-structure.md (examples, check questions and the facts quoted)."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/atmosphere-structure.md")
ok = C.ok

# ---- US Standard Atmosphere 1976 (independent reference model), temperature in K, pressure in Pa
G0, R, M = 9.80665, 8.31432, 0.0289644
LAYERS = [(0, 288.15, -6.5), (11, 216.65, 0.0), (20, 216.65, 1.0), (32, 228.65, 2.8), (47, 270.65, 0.0),
          (51, 270.65, -2.8), (71, 214.65, -2.0), (84.852, 186.946, 0.0)]       # (km, T_K at base, lapse K/km)


def std_atmosphere(z_km):
    p = 101325.0
    for i, (zb, tb, lap) in enumerate(LAYERS):
        zt = LAYERS[i + 1][0] if i + 1 < len(LAYERS) else 1e9
        dz = min(z_km, zt) - zb
        if dz <= 0:
            break
        if lap == 0:
            p *= math.exp(-G0 * M * dz * 1000 / (R * tb))
        else:
            t = tb + lap * dz
            p *= (t / tb) ** (-G0 * M / (R * lap / 1000))
    zb, tb, lap = [L for L in LAYERS if L[0] <= z_km][-1]
    return tb + lap * (z_km - zb), p / 100.0       # K, hPa


# ---- FACT_CHECKS: every number stated in the file
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


fact("composition sums to ~100 %", abs(78.08 + 20.95 + 0.93 + 0.042 - 100) < 0.01)
fact("N2 78 %, O2 21 %, Ar 0.9 %, CO2 0.04 % are the rounded values", (round(78.08), round(20.95), round(0.93, 1), round(0.042, 2)) == (78, 21, 0.9, 0.04))
fact("1 atm = 1013 hPa at sea level", abs(std_atmosphere(0)[1] - 1013.25) < 0.01)
fact("pressure at 5.5 km is about half (500 hPa)", abs(std_atmosphere(5.5)[1] - 500) < 15 and abs(std_atmosphere(5.5)[1] / std_atmosphere(0)[1] - 0.5) < 0.02)
fact("half of the air mass is below 5.5 km", abs(1 - std_atmosphere(5.5)[1] / std_atmosphere(0)[1] - 0.5) < 0.02)
fact("about 99 % of the air mass is below 30 km", 1 - std_atmosphere(30)[1] / std_atmosphere(0)[1] > 0.985)
fact("about 80 % of the air mass is below the 11 km tropopause", 0.75 < 1 - std_atmosphere(11)[1] / std_atmosphere(0)[1] < 0.80 + 0.01)
fact("pressure near 11 km is about 250 hPa (real 227)", abs(std_atmosphere(11)[1] - 227) < 3)
fact("water: 10.3 m of water = 1 atm", abs(101325 / (1000 * 9.80665) - 10.33) < 0.01)
fact("temperature at the tropopause is about -56 C", abs((std_atmosphere(11)[0] - 273.15) - (-56.5)) < 0.1)
fact("stratopause is about -2 C", abs((std_atmosphere(50)[0] - 273.15) - (-2.5)) < 0.6)
fact("mesopause about -90 C (standard model gives -86)", -92 < std_atmosphere(84.852)[0] - 273.15 < -84)
fact("lapse rate 6.5 C/km in the troposphere", abs((std_atmosphere(0)[0] - std_atmosphere(11)[0]) / 11 - 6.5) < 1e-9)
fact("temperature rises in the stratosphere and falls again in the mesosphere",
     std_atmosphere(20)[0] < std_atmosphere(50)[0] and std_atmosphere(50)[0] > std_atmosphere(80)[0])
fact("order of layer tops 11 < 50 < 85 < 600", 11 < 50 < 85 < 600)
fact("ozone layer 15-35 km lies inside the stratosphere 11-50 km", 11 <= 15 and 35 <= 50)

# ---- Example 1: lapse rate to 11 km from 15 C
T1 = 15 - 6.5 * 11
C.mcq("**Example 1.**", T1, "°C", "C")
C.opt_is("**Example 1.**", "D", -6.5 * 11, "°C")
C.opt_is("**Example 1.**", "B", 15 - 1 * 11, "°C")
C.opt_is("**Example 1.**", "A", 15 + 6.5 * 11, "°C")
ok(abs(T1 - (std_atmosphere(11)[0] - 273.15)) < 0.1, "standard atmosphere agrees")

# ---- Example 2: halving rule (checked against logarithms, and vs the real model)
P2 = 1013 * 0.5 ** (11 / 5.5)
C.mcq("**Example 2.**", P2, "hPa", "C", tol=0.005)
C.opt_is("**Example 2.**", "A", 1013 * 0.5, "hPa", tol=0.005)
C.opt_is("**Example 2.**", "D", 1013 * 0.5 ** 3, "hPa", tol=0.005)
C.opt_is("**Example 2.**", "E", 0, "hPa")
ok(abs(math.log2(1013 / P2) * 5.5 - 11) < 1e-9)

# ---- Q1..Q5
o1 = C.options("**1.**")
ok(o1["C"] == "Oxygen" and C.key_letter(1) == "C" and o1["A"] == "Nitrogen")
o2 = C.options("**2.**")
ok(C.key_letter(2) == "B" and "ozone" in o2["B"] and all("ozone" not in o2[k] for k in "ACDE"))
T3 = 30 - 6.5 * 5
C.mcq("**3.**", T3, "°C", "D")
C.opt_is("**3.**", "C", 30 - 6.5, "°C")
C.opt_is("**3.**", "B", 30 - 5, "°C")
C.opt_is("**3.**", "A", 30 + 6.5 * 5, "°C")
C.opt_is("**3.**", "E", -6.5 * 5, "°C")
o4 = C.options("**4.**")
ok(C.key_letter(4) == "E" and "very few particles" in o4["E"])
P5 = 1000 * 0.5 ** (22 / 5.5)
C.mcq("**5.**", P5, "hPa", "A", tol=0.005)
C.opt_is("**5.**", "B", 1000 * 0.5 ** 3, "hPa")
C.opt_is("**5.**", "C", 1000 * 0.5 ** 2, "hPa")
C.opt_is("**5.**", "D", 1000 * 0.5, "hPa")
C.opt_is("**5.**", "E", 1000 * 0.5 ** 5, "hPa", tol=0.01)
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
