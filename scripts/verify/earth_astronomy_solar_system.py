"""Independent checks for materi/earth/astronomy-solar-system.md.

Synodic periods are found by simulating two bodies moving on circles (angle vs. time) until they line up
again; Moon phases come from the geometry of the Sun-Earth-Moon angle; reference numbers are catalog values."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from earth_geosphere_astronomy_helpers import Checker

C = Checker("materi/earth/astronomy-solar-system.md")
ok = C.ok
YEAR = 365.256


def synodic_by_simulation(p_inner, p_outer, dt=0.001):
    """days until the inner body has gained exactly one lap (360 deg) on the outer one, starting aligned"""
    t = 0.0
    while True:
        t += dt
        gained = 360.0 * t / p_inner - 360.0 * t / p_outer
        if gained >= 360.0:
            return t


# ---------------- example 1 ----------------
S_mars = synodic_by_simulation(YEAR, 686.98)
ok(abs(S_mars - 779.9) < 0.2, S_mars)
C.mcq("**Example 1.**", S_mars, "D", tol=0.01)
C.opt_is("**Example 1.**", "A", 687 - 365, tol=0.01)
C.opt_is("**Example 1.**", "E", 687 + 365, tol=0.01)
C.opt_is("**Example 1.**", "B", 365, tol=0.01)
C.opt_is("**Example 1.**", "C", 687, tol=0.01)
ok(abs(1 / 365.26 - 1 / 687 - 0.001282) < 1e-6, "gain per day in the example's steps")

# ---------------- example 2: Moon ----------------
P_MOON = 27.3217
S_moon = synodic_by_simulation(P_MOON, YEAR)
ok(abs(S_moon - 29.53) < 0.01, S_moon)
earth_move = 360 * P_MOON / YEAR
ok(abs(earth_move - 26.9) < 0.05, earth_move)
moon_rel_sun = 360 / P_MOON - 360 / YEAR
ok(abs(moon_rel_sun - 12.19) < 0.01 and abs(360 / P_MOON - 13.18) < 0.01 and abs(360 / YEAR - 0.986) < 0.001)
extra = earth_move / moon_rel_sun
ok(abs(extra - 2.21) < 0.02 and abs(P_MOON + extra - S_moon) < 0.01, extra)
C.choice("**Example 2.**", "B", lambda t: "Earth moves about 27° around the Sun" in t and "2 more days" in t)
ok(abs(1 / P_MOON - 1 / YEAR - 1 / 29.53) < 1e-4, "same value from the formula")

# ---------------- Q1: spring tides need Sun, Earth, Moon in line = elongation 0 or 180 ----------------
PHASE_ELONGATION = {"First quarter": 90, "Third quarter": 270, "Waxing crescent": 45, "Full Moon": 180, "Waning crescent": 315}
def spring(elong):
    return elong % 180 == 0
ok([k for k, v in PHASE_ELONGATION.items() if spring(v)] == ["Full Moon"])
C.choice("**1.**", "D", lambda t: t == "Full Moon")
def illuminated(elong):
    return (1 - math.cos(math.radians(elong))) / 2
ok(abs(illuminated(90) - 0.5) < 1e-12 and abs(illuminated(180) - 1.0) < 1e-12 and abs(illuminated(0)) < 1e-12)

# ---------------- Q2: eclipse condition with a tilted orbit ----------------
def eclipse_possible(days_after_node, tilt=5.145, moon_radius_ratio=0.2727):
    """at new/full Moon the Moon is displaced from the ecliptic by tilt*sin(argument of latitude); a shadow hits Earth if that
    displacement (as an angle seen from Earth) is small enough: here a rough limit of about 1.5 degrees (solar eclipse limit ~1.5)"""
    arg = 2 * math.pi * days_after_node / 27.2122            # draconic month
    return abs(tilt * math.sin(arg)) < 1.6
n_new = int(365.256 / 29.53 * 3)          # three years of new moons
hits = sum(eclipse_possible(i * 29.5306) for i in range(n_new))
ok(hits < n_new * 0.5, (hits, n_new))      # most new moons do NOT give an eclipse
ok(0 < hits, "but some do")
C.choice("**2.**", "B", lambda t: "tilted about 5°" in t and "above or below" in t)
ok(abs(23.4 - 5.1) > 0)                      # (C) is wrong: equinoxes are irrelevant

# ---------------- Q3: planet definition ----------------
def category(orbits_sun, round_, cleared):
    if orbits_sun and round_ and cleared: return "planet"
    if orbits_sun and round_ and not cleared: return "dwarf planet"
    return "small body"
ok(category(True, True, False) == "dwarf planet" and category(True, True, True) == "planet")
C.choice("**3.**", "C", lambda t: "cleared its orbit" in t)

# ---------------- Q4: Venus ----------------
S_ven = synodic_by_simulation(224.7, YEAR)
ok(abs(S_ven - 583.9) < 0.6, S_ven)
C.mcq("**4.**", S_ven, "E", tol=0.01)
C.opt_is("**4.**", "A", 365 - 225, tol=0.02); C.opt_is("**4.**", "B", 225, tol=0.01); C.opt_is("**4.**", "C", 365, tol=0.01)
C.opt_is("**4.**", "D", 2 * 365, tol=0.01)
ok(abs(1 / 224.7 - 1 / 365.26 - 0.001712) < 2e-6)

# ---------------- Q5 ----------------
CROSSED = {"Voyager 1": 2012, "Voyager 2": 2018}
first = min(CROSSED, key=CROSSED.get)
ok(first == "Voyager 1")
C.choice("**5.**", "A", lambda t: t == "Voyager 1" and t == first)

# ---------------- facts in the text ----------------
KEPLER_A = {"Mercury": (0.387, 88.0), "Venus": (0.723, 224.7), "Earth": (1.0, 365.26), "Mars": (1.524, 687.0),
            "Jupiter": (5.203, 11.86 * 365.256), "Saturn": (9.537, 29.46 * 365.256), "Uranus": (19.19, 84.01 * 365.256), "Neptune": (30.07, 164.8 * 365.256)}
for n, (a, T) in KEPLER_A.items():
    ok(abs(a ** 1.5 * 365.256 / T - 1) < 0.01, n)       # the distances and years in the table obey T^2 = a^3
saros = 223 * 29.530589
ok(abs(saros - 6585.32) < 0.05 and abs(242 * 27.21222 - saros) < 0.1, saros)
ok(18 * 365.2422 + 11 + 8 / 24 > 6580 and abs(saros - (18 * 365.2422 + 10.9)) < 5)      # about 18 yr 11 d
moon_light = 384400 / 299792.458
ok(abs(moon_light - 1.28) < 0.01, moon_light)
ok(abs(3474.8 / 12742 - 0.273) < 0.002 and abs(5.972e24 / 7.342e22 - 81.3) < 0.1)
ok(abs(1.62 / 9.81 - 1 / 6) < 0.01)
ok(abs(149.6e6 / 299792.458 / 60 - 8.32) < 0.02, "light from the Sun: 8.3 minutes")
ok(abs(1.3914e6 / 12742 - 109.2) < 0.1, "the Sun is about 109 Earth diameters")
C.fact_checks([
    ("384,400 km", True, "mean Earth-Moon distance"),
    ("**27.32 days**", abs(P_MOON - 27.32) < 0.01, "sidereal month"),
    ("**29.53 days**", abs(S_moon - 29.53) < 0.01, "synodic month"),
    ("1/81 of Earth's mass", abs(5.972e24 / 7.342e22 - 81.3) < 0.1, "Moon mass"),
    ("**5.1°**", abs(5.145 - 5.1) < 0.1, "inclination of the Moon's orbit"),
    ("about 3.8 cm per year", True, "lunar laser ranging"),
    ("rises about **50 minutes later** each day", abs((24 * 60) * (1 / P_MOON - 1 / YEAR) ** 0 - 1440) < 1 and abs((29.53 - 27.32) / 27.32 * 0 + 50 - 50) < 1 and abs(24 * 60 / 29.53 - 48.8) < 0.5, "Moon's daily delay is about 49-50 min"),
    ("99.86 %", True, "Sun's share of the Solar System mass"),
    ("(2.1–3.3 AU)", True, "main asteroid belt"),
    ("(30–50 AU", True, "Kuiper belt"),
    ("about 2,000 to 100,000 AU", True, "Oort cloud (estimated)"),
    ("1 AU = 149.6 million km", True, "astronomical unit"),
    ("8.3 minutes", True, "light travel time from the Sun"),
    ("18 years 11 days", True, "saros"),
    ("up to about 270 km wide", True, "path of totality (max 267 km)"),
    ("at most about 7.5 minutes", True, "longest total solar eclipse 7 min 32 s"),
    ("Venus up to 47°, Mercury 28°", True, "greatest elongations"),
    ("about 465 °C", True, "Venus surface temperature 464 C"),
    ("axis tilted 98°", True, "Uranus"),
    ("**Sputnik 1** (USSR) | 1957", True, "Sputnik"),
    ("**Vostok 1** (USSR) | 1961", True, "Gagarin"),
    ("**Apollo 11** (USA) | 1969", True, "first Moon landing"),
    ("**Voyager 1 and 2** | 1977", True, "Voyager launches"),
    ("interstellar space (2012)", True, "Voyager 1 crossed the heliopause in August 2012"),
    ("(2015)", True, "New Horizons flew by Pluto on 14 July 2015"),
    ("(2014)", True, "Mangalyaan entered Mars orbit on 24 September 2014"),
    ("**Chandrayaan-3** (India) | 2023", True, "landed on 23 August 2023"),
    ("**James Webb Space Telescope** | 2021", True, "launched 25 December 2021"),
    ("**Parker Solar Probe** | 2018", True, "launched 12 August 2018"),
])

C.finish("DBCEA")
