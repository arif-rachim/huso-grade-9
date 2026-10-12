"""Independent checks for materi/earth/hydrosphere-freshwater.md (discharge, continuity, pool filling, water inventory)."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/earth/hydrosphere-freshwater.md")
ok = C.ok
FACT_CHECKS = []


def fact(name, cond):
    FACT_CHECKS.append(name)
    ok(cond, name)


# ---- hook: pool filling
pool = 25 * 10 * 2
fact("pool is 500 m3", pool == 500)
days_hose = pool * 1000 / 0.3 / 86400
fact("hose at 0.3 L/s takes about 19 days", abs(days_hose - 19.3) < 0.1)
fact("100 m3/s fills the pool in 5 s", pool / 100 == 5)

# ---- Example 1: discharge by summing thin vertical slices (1 cm wide strips) of the cross-section
w, d, L, t = 12.0, 1.5, 20.0, 16.0
v_surface = L / t
v_mean = 0.85 * v_surface
slices = 1200
Q = sum((w / slices) * d * v_mean for _ in range(slices))
fact("Example 1: v_surface 1.25 m/s, v_mean 1.0625 m/s, area 18 m2", abs(v_surface - 1.25) < 1e-12 and abs(v_mean - 1.0625) < 1e-12 and abs(w * d - 18) < 1e-12)
fact("Example 1: Q = 19.1 m3/s", abs(Q - 19.125) < 1e-6)
C.mcq("**Example 1.**", Q, "m³/s", "B", tol=0.01)
C.opt_is("**Example 1.**", "C", w * d * v_surface, "m³/s", tol=0.01)
C.opt_is("**Example 1.**", "A", w * d * (t / L), "m³/s", tol=0.01)
C.opt_is("**Example 1.**", "D", w * d * 0.85, "m³/s", tol=0.01)
C.opt_is("**Example 1.**", "E", Q / 10, "m³/s", tol=0.01)

# ---- Example 2: continuity
Q2 = 20 * 2 * 0.5
v2 = Q2 / (8 * 2.5)
fact("Example 2: Q = 20 m3/s, v = 1.0 m/s", Q2 == 20 and abs(v2 - 1.0) < 1e-12)
C.mcq("**Example 2.**", v2, "m/s", "C")
C.opt_is("**Example 2.**", "D", 0.5 * 20 / 8, "m/s")
C.opt_is("**Example 2.**", "A", 0.5 * 2 / 2.5, "m/s")
C.opt_is("**Example 2.**", "B", 0.5, "m/s")
C.opt_is("**Example 2.**", "E", 20 / 8, "m/s")
fact("narrower and shallower speeds up; wider and deeper slows down", Q2 / (4 * 1) > 0.5 and (10 * 1.5 * 0.8) / (12 * 2) < 0.8)

# ---- Q1 pool at 2.5 m3/s
t1 = pool / 2.5
C.mcq("**1.**", t1, "s", "C")
C.opt_is("**1.**", "A", 2.5 / pool, "s", tol=0.01)
C.opt_is("**1.**", "B", pool / 25, "s")
C.opt_is("**1.**", "D", 500, "s")
C.opt_is("**1.**", "E", pool * 2.5, "s")

# ---- Q5 continuity
Q5 = 10 * 1.5 * 0.8
v5 = Q5 / (12 * 2)
fact("Q5: Q = 12 m3/s, v = 0.5 m/s", abs(Q5 - 12) < 1e-12 and abs(v5 - 0.5) < 1e-12)
C.mcq("**5.**", v5, "m/s", "B")
C.opt_is("**5.**", "A", 0.4, "m/s")
C.opt_is("**5.**", "C", 0.8, "m/s")
C.opt_is("**5.**", "D", 1.0, "m/s")
C.opt_is("**5.**", "E", 1.6, "m/s")
fact("Q5 explanation: (E) 1.6 = 2 x 0.8", abs(1.6 - 2 * 0.8) < 1e-12)

# ---- units
fact("1 m3/s = 1000 L/s, so 2.4 m3/s is 2400 L/s", 2.4 * 1000 == 2400)

# ---- hydrograph: a toy unit hydrograph. Paved area: runoff coefficient bigger, travel time shorter -> higher, earlier peak
def peak_and_lag(runoff_coeff, travel_hours, rain_mm=40, area_km2=10):
    # instantaneous rain at t=0; runoff volume released uniformly over `travel_hours`... triangular response
    vol = runoff_coeff * rain_mm / 1000 * area_km2 * 1e6          # m3
    base = 2 * travel_hours * 3600
    peak = 2 * vol / base                                         # triangle area = vol
    return peak, travel_hours


p_farm, lag_farm = peak_and_lag(0.25, 6)
p_city, lag_city = peak_and_lag(0.75, 2)
fact("paved city: higher peak and shorter lag than farmland", p_city > p_farm and lag_city < lag_farm)
o4 = C.options("**4.**")
fact("Q4 key D = higher peak, shorter lag", C.key_letter(4) == "D" and o4["D"] == "a higher peak and a shorter lag time.")

# ---- Q2, Q3
o2 = C.options("**2.**")
fact("Q2 key E = inside of the bend, slow", C.key_letter(2) == "E" and o2["E"] == "inside of the bend, where the water is slow.")
# meander speed: speed ~ 1/radius of curvature around the bend (free vortex): inside is faster in a simple vortex, but in real rivers the thalweg shifts outside
fact("real channels: fastest and deepest water (thalweg) swings to the outside (as written)", "fastest water swings to the **outside**" in C.txt)
o3 = C.options("**3.**")
fact("Q3 key A = delta where river enters standing water and slows", C.key_letter(3) == "A" and "slows down" in o3["A"])

# ---- inventory of water (USGS style numbers, km3)
TOTAL, OCEAN, FRESH = 1.386e9, 1.338e9, 35.03e6
ICE, GW = 24.064e6, 10.53e6
fact("oceans 96.5 % of all water", abs(OCEAN / TOTAL * 100 - 96.5) < 0.1)
fact("fresh water about 2.5 % of all water", abs(FRESH / TOTAL * 100 - 2.5) < 0.1)
fact("ice 68.7 % of fresh, groundwater 30.1 %, rest about 1.2 %", abs(ICE / FRESH * 100 - 68.7) < 0.1 and abs(GW / FRESH * 100 - 30.1) < 0.1 and abs(100 - ICE / FRESH * 100 - GW / FRESH * 100 - 1.2) < 0.15)
fact("rivers 2120 km3 are about 0.006 % of fresh water", abs(2120 / FRESH * 100 - 0.006) < 0.001)
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
print(len(FACT_CHECKS), "fact checks")
C.done()
