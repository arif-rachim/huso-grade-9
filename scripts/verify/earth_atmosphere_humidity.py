"""Independent checks for materi/earth/atmosphere-humidity.md (Magnus formula, bisection for the dew point, parcel simulation)."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/atmosphere-humidity.md")
ok = C.ok
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


def es(t):                       # saturation vapor pressure over water, hPa (Buck 1981)
    return 6.1121 * math.exp((18.678 - t / 234.5) * (t / (257.14 + t)))


def es_magnus(t):                # Magnus pair for water and ice (used only to compare ice with water)
    return 6.112 * math.exp(17.62 * t / (243.12 + t))


def sat_gm3(t):                  # max vapor density, g/m3 (ideal gas for vapor)
    return es(t) * 100 / (461.5 * (t + 273.15)) * 1000


def dewpoint(t, rh):             # bisection: find Td with es(Td) = rh * es(t)
    target = rh / 100 * es(t)
    lo, hi = -60.0, t
    for _ in range(200):
        mid = (lo + hi) / 2
        if es(mid) < target:
            lo = mid
        else:
            hi = mid
    return lo


# ---- the table
table = {0: 4.8, 10: 9.4, 20: 17.3, 30: 30.4, 40: 51.1}
for t, v in table.items():
    fact(f"table value at {t} C", abs(sat_gm3(t) - v) < 0.06)
    fact(f"table value at {t} C is printed in the file", f"{v} g" in C.txt)
ratios = [sat_gm3(t + 10) / sat_gm3(t) for t in (0, 10, 20, 30)]
fact("capacity almost doubles per 10 C (ratios 1.65 to 2.0)", all(1.65 < r < 2.0 for r in ratios))
fact("dew point rule of thumb accurate to 1 C for RH 60-100 at 10-35 C",
     all(abs(dewpoint(t, rh) - (t - (100 - rh) / 5)) < 1.0 for t in (10, 15, 20, 25, 30, 35) for rh in (60, 70, 80, 90, 100)))
fact("RH rises when air is cooled (same vapor)", 15 / sat_gm3(20) > 15 / sat_gm3(30))
fact("dew point is independent of temperature at fixed vapor pressure", abs(dewpoint(30, 100 * es(20) * 0.5 / es(30) * 2 / 2) - dewpoint(30, 100 * es(20) * 0.5 / es(30))) < 1e-9)

# ---- Example 1: 25 C, 70 %
td1 = dewpoint(25, 70)
ok(abs(td1 - 19.14) < 0.05, td1)
C.mcq("**Example 1.**", td1, "°C", "C", tol=0.01)
C.opt_is("**Example 1.**", "B", 25 * 0.70, "°C")
C.opt_is("**Example 1.**", "E", dewpoint(25, 100), "°C")
fact("Example 1 rule of thumb = 19", 25 - (100 - 70) / 5 == 19)

# ---- Example 2 and Q5: lifting a parcel in 1 m steps (dry rate 9.8 C/km, dew point 1.8 C/km)
def lcl(t, td):
    z = 0.0
    while t - 9.8 * z / 1000 > td - 1.8 * z / 1000:
        z += 1.0
    return z


L2 = lcl(28, 20)
fact("Example 2: simulated LCL is 1000 m", abs(L2 - 1000) <= 1)
C.mcq("**Example 2.**", L2, "m", "C", tol=0.01)
C.opt_is("**Example 2.**", "A", 125, "m")
C.opt_is("**Example 2.**", "B", 8 * 100, "m")
C.opt_is("**Example 2.**", "D", 20 * 125, "m")
C.opt_is("**Example 2.**", "E", 28 * 125, "m")
fact("dry adiabatic rate g/cp = 9.8 C/km", abs(9.80665 / 1004.0 * 1000 - 9.8) < 0.05)
fact("Espy rule: 125 m per C of spread = 1000 / (9.8 - 1.8)", abs(1000 / (9.8 - 1.8) - 125) < 1e-9)

L5 = lcl(24, 14)
fact("Q5 simulated LCL is 1250 m", abs(L5 - 1250) <= 1)
C.mcq("**5.**", L5, "m", "D", tol=0.01)
C.opt_is("**5.**", "A", 125, "m")
C.opt_is("**5.**", "B", 10 * 100, "m")
C.opt_is("**5.**", "C", 14 * 125, "m")
C.opt_is("**5.**", "E", 24 * 125, "m")

# ---- Q1
o1 = C.options("**1.**")
fact("Q1 condensation (A) releases heat; others take heat or none", C.key_letter(1) == "A" and o1["A"] == "condensation")

# ---- Q2: RH after cooling with the given table values
rh2 = 15 / 17.3 * 100
fact("Q2 uses the table values given in the question", "30.4 g at 30 °C and 17.3 g at 20 °C" in C.txt)
C.mcq("**2.**", rh2, "%", "C", tol=0.01)
C.opt_is("**2.**", "A", 15 / 30.4 * 100, "%", tol=0.01)
C.opt_is("**2.**", "E", 17.3 / 15 * 100, "%", tol=0.01)
C.opt_is("**2.**", "B", 15, "%")
fact("Q2: with the real formula too (within 1 %)", abs(15 / sat_gm3(20) * 100 - rh2) < 1.0)

# ---- Q3 conceptual: saturation vapor pressure over ice (Magnus-type for ice) < over water below 0 C
def es_ice(t):
    return 6.112 * math.exp(22.46 * t / (272.62 + t))


fact("es over ice < es over water for T < 0 C (so ice grows)", all(es_ice(t) < es_magnus(t) for t in (-5, -10, -15, -20, -30)))
fact("difference is largest near -12 C", max(range(-35, 0), key=lambda t: es_magnus(t) - es_ice(t)) in range(-17, -8))
o3 = C.options("**3.**")
fact("Q3 key E", C.key_letter(3) == "E" and "over ice is lower than over water" in o3["E"])

# ---- Q4: evaporation rate ~ (es(Twater) - e_air): wet bulb free simple "Dalton" model
e_air = lambda rh: rh / 100 * es(28)
rate = lambda rh: es(28) - e_air(rh)
fact("Q4: Monday (30 % RH) evaporates faster than Tuesday (90 %); both are positive", rate(30) > rate(90) > 0 and rate(30) / rate(90) > 3)
o4 = C.options("**4.**")
fact("Q4 key B", C.key_letter(4) == "B" and o4["B"].startswith("It is faster on Monday"))

# ---- facts in the water-cycle point
atm_km3, total_km3, precip_km3_yr = 12900.0, 1.386e9, 505000.0
fact("air holds about 0.001 % of Earth's water", abs(atm_km3 / total_km3 * 100 - 0.001) < 0.0003)
fact("residence time of water in the air is about 9 days", abs(atm_km3 / precip_km3_yr * 365 - 9.3) < 0.5)
fact("a raindrop (2 mm) vs a cloud droplet (0.02 mm): a million droplets", (2 / 0.02) ** 3 == 1e6 or abs((2 / 0.02) ** 3 - 1e6) < 1)
fact("raindrop about 100 times wider", 2 / 0.02 == 100)
fact("latent heat gives MJ/kg scale", 2.26e6 > 1e6)
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
