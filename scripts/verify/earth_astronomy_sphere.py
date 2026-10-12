"""Independent checks for materi/earth/astronomy-sphere.md.

Altitudes are computed from spherical astronomy (the sin h formula) by sampling a whole day, not by the
shortcut formulas used in the text. Star data are catalog values (Hipparcos/Gaia parallaxes, J2000 positions)."""
import sys, pathlib, math, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from earth_geosphere_astronomy_helpers import Checker

C = Checker("materi/earth/astronomy-sphere.md")
ok = C.ok
D2R = math.pi / 180


def altitude(phi, dec, H):
    """altitude in degrees for latitude phi, declination dec, hour angle H (all degrees)"""
    s = math.sin(phi * D2R) * math.sin(dec * D2R) + math.cos(phi * D2R) * math.cos(dec * D2R) * math.cos(H * D2R)
    return math.degrees(math.asin(s))


def day_range(phi, dec):
    alts = [altitude(phi, dec, h / 10.0) for h in range(3600)]
    return min(alts), max(alts)


# ---------------- example 1: latitude 40 N, dec +55 ----------------
lo, hi = day_range(40, 55)
ok(abs(lo - 5.0) < 0.01 and abs(hi - 75.0) < 0.01, (lo, hi))
sets = lo < 0
ok(not sets)
def parse1(t):
    never = "never sets" in t
    alt = float(re.search(r"altitude is (−?\d+)", t).group(1).replace("−", "-"))
    return never, alt
C.choice("**Example 1.**", "B", lambda t: parse1(t) == (not sets, round(lo)))
ok(abs(abs(40 - 55) - 15) < 1e-9 and 55 == 55)                 # distractors C and E
ok(55 - 50 == 5 and 50 - 55 == -5 and 35 - 50 == -15)           # (A) and (D) sign errors
# threshold: circumpolar iff lowest altitude > 0  <=>  dec > 90 - phi
for d in (49, 49.9, 50.1, 51):
    ok((day_range(40, d)[0] > 0) == (d > 90 - 40), d)
# stars that never rise
ok(day_range(40, -51)[1] < 0 and day_range(40, -49)[1] > 0)

# ---------------- example 2: parallax ----------------
p = 0.050
d_pc = 1 / p
d_ly = d_pc * 3.2616
ok(abs(d_pc - 20) < 1e-12 and abs(d_ly - 65.2) < 0.1)
C.mcq("**Example 2.**", d_ly, "D")
C.opt_is("**Example 2.**", "C", d_pc)
C.opt_is("**Example 2.**", "A", p * 3.2616, tol=0.03)
C.opt_is("**Example 2.**", "B", (1 / 0.5) * 3.2616)
C.opt_is("**Example 2.**", "E", (1 / 0.005) * 3.2616, tol=0.01)    # parallax read as 0.005'' -> ~650 ly

# parsec definition: 1 AU subtends 1 arcsecond at 1 pc
AU_PER_PC = 1 / math.tan(math.radians(1 / 3600))
ok(abs(AU_PER_PC - 206265) < 1, AU_PER_PC)
ly_per_pc = AU_PER_PC * 149597870.7 / 9460730472580.8
ok(abs(ly_per_pc - 3.2616) < 1e-3)

# ---------------- check questions ----------------
# Q1: latitude 6 S (-6)
phi = -6.0
ncp_alt, scp_alt = phi, -phi
pol_ra_dec = (2.5300, 89.264)
polaris_max = day_range(phi, pol_ra_dec[1])[1]
ok(polaris_max < 0, "Polaris never gets above the horizon at 6 S")
ok(abs(ncp_alt + 6) < 1e-9 and abs(scp_alt - 6) < 1e-9)
def q1(t):
    if t.startswith("The south celestial pole is "):
        return ("6° above the south horizon" in t) and abs(scp_alt - 6) < 1e-9
    return False
C.choice("**1.**", "B", q1)
ok(abs((90 - 6) - 84) < 1e-9)       # (D): that is the altitude of the celestial equator

# Q2: Sun at the March equinox: ecliptic longitude 0
EPS = 23.4393
def sun(lam):
    dec = math.degrees(math.asin(math.sin(EPS * D2R) * math.sin(lam * D2R)))
    ra = math.degrees(math.atan2(math.cos(EPS * D2R) * math.sin(lam * D2R), math.cos(lam * D2R))) % 360 / 15
    return ra, dec
ok(all(abs(a - b) < 1e-9 for a, b in zip(sun(0), (0, 0))), sun(0))
ok(abs(sun(90)[0] - 6) < 1e-9 and abs(sun(90)[1] - 23.44) < 0.01)
ok(abs(sun(180)[0] - 12) < 1e-9 and abs(sun(270)[0] - 18) < 1e-9 and abs(sun(270)[1] + 23.44) < 0.01)
def q2(t):
    return "celestial equator" in t and "day and night" in t
C.choice("**2.**", "E", q2)

# Q3: type of M45
OBJ = {"M42": "emission nebula", "M31": "spiral galaxy", "M1": "supernova remnant", "M45": "open cluster", "M13": "globular cluster"}
C.choice("**3.**", "A", lambda t: t == "open cluster" and OBJ["M45"] == "open cluster")
ok(set(OBJ[k] for k in ("M42", "M31", "M1", "M45")) == {"emission nebula", "spiral galaxy", "supernova remnant", "open cluster"})

# Q4
dA, dB = 1 / 0.20, 1 / 0.04
ok(abs(dB / dA - 5) < 1e-12)
C.choice("**4.**", "C", lambda t: t == "B is 5 times farther than A" and abs(dB / dA - 5) < 1e-12)

# Q5
lo5, hi5 = day_range(50, 20)
ok(abs(hi5 - 60) < 0.01, hi5)
C.mcq("**5.**", hi5, "D")
ok(50 - 20 == 30 and 90 - 50 == 40 and 50 + 20 == 70)         # distractors B, C, E

# ---------------- facts in the text ----------------
# parallaxes in arcseconds (Hipparcos / Gaia) -> distance in light-years
PLX = {"Sirius": 0.37921, "Vega": 0.13023, "Proxima": 0.76813, "Rigel": 0.00378, "Polaris": 0.00754}
def ly(name):
    return 1 / PLX[name] * ly_per_pc
ok(abs(ly("Sirius") - 8.6) < 0.1 and abs(ly("Vega") - 25) < 0.5 and abs(ly("Proxima") - 4.24) < 0.02)
ok(abs(ly("Rigel") - 860) < 20 and abs(ly("Polaris") - 430) < 10)
ok(abs(1 / 0.77 - 1.3) < 0.01 and abs(1 / 0.77 * 3.26 - 4.2) < 0.05, "Proxima: p = 0.77'' -> 1.3 pc -> 4.2 ly")
MAG = {"Sirius": -1.46, "Betelgeuse": 0.4, "Rigel": 0.13, "Vega": 0.03, "Proxima": 11.1, "Polaris": 1.98}
ok(min(MAG, key=MAG.get) == "Sirius", "Sirius is the brightest")
ok(MAG["Proxima"] > 6, "Proxima is invisible to the naked eye")

# positions (RA hours, Dec deg) of the stars drawn in the SVGs, to check constellation membership and circumpolarity
POS = {"Dubhe": (11.062, 61.75), "Polaris": (2.53, 89.26), "Vega": (18.615, 38.78), "Schedar": (0.675, 56.54),
       "Betelgeuse": (5.92, 7.41), "Rigel": (5.242, -8.2), "Sirius": (6.752, -16.72)}
ok(POS["Dubhe"][1] > 90 - 40 and POS["Vega"][1] < 90 - 40, "Dubhe is circumpolar at 40 N, Vega is not")
ok(abs(POS["Polaris"][1] - 90) < 1.0, "Polaris within 1 degree of the pole")
ok(POS["Betelgeuse"][1] > 0 > POS["Rigel"][1], "Betelgeuse north of the equator, Rigel south")

ZODIAC = ["Ari", "Tau", "Gem", "Cnc", "Leo", "Vir", "Lib", "Sco", "Sgr", "Cap", "Aqr", "Psc"]
NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpius", "Sagittarius", "Capricornus", "Aquarius", "Pisces"]
ok(len(ZODIAC) == len(NAMES) == 12)

C.fact_checks([
    ("(0h–24h, 1h = 15°)", 24 * 15 == 360, "RA hours to degrees"),
    ("**23.4°**", abs(EPS - 23.4) < 0.05, "obliquity of the ecliptic"),
    ("**h = 90° − |φ − δ|**", abs(day_range(30, 10)[1] - (90 - abs(30 - 10))) < 0.01, "upper culmination altitude"),
    ("**90° − φ**", True, "altitude of the celestial equator on the meridian"),
    ("**δ > 90° − φ**", True, "circumpolar condition"),
    ("**δ + φ − 90°**", abs(day_range(40, 55)[0] - (55 + 40 - 90)) < 0.01, "lowest altitude"),
    ("**~20 March**", True, "March equinox 2026 is on 20 March"),
    ("**~21 June**", True, "June solstice 2026 is on 21 June"),
    ("**~21 December**", True, "December solstice 2026 is on 21 December"),
    ("One parsec = 3.26 light-years = 206,265 AU", abs(AU_PER_PC - 206265) < 1 and abs(ly_per_pc - 3.26) < 0.01, "definition of the parsec"),
    ("8.6 ly", abs(ly("Sirius") - 8.6) < 0.1, "Sirius parallax"),
    ("| 25 ly |", abs(ly("Vega") - 25) < 0.5, "Vega parallax"),
    ("4.24 ly", abs(ly("Proxima") - 4.24) < 0.02, "Proxima parallax"),
    ("about 860 ly", abs(ly("Rigel") - 860) < 20, "Rigel parallax"),
    ("about 430 ly", abs(ly("Polaris") - 430) < 10, "Polaris parallax"),
    ("−1.46", MAG["Sirius"] == -1.46, "Sirius magnitude"),
    ("**M42** Orion Nebula", OBJ["M42"] == "emission nebula", "Messier catalog"),
    ("**M31** Andromeda Galaxy", OBJ["M31"] == "spiral galaxy", "Messier catalog"),
    ("**M1** Crab Nebula", OBJ["M1"] == "supernova remnant", "Messier catalog (SN 1054)"),
    ("exploded in the year 1054", True, "SN 1054"),
    ("**M45** Pleiades", OBJ["M45"] == "open cluster", "Messier catalog"),
    ("Ari, Tau, Gem, Cnc, Leo, Vir, Lib, Sco, Sgr, Cap, Aqr, Psc", ", ".join(ZODIAC) == "Ari, Tau, Gem, Cnc, Leo, Vir, Lib, Sco, Sgr, Cap, Aqr, Psc", "IAU abbreviations"),
    ("Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpius, Sagittarius, Capricornus, Aquarius, Pisces", ", ".join(NAMES) == "Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpius, Sagittarius, Capricornus, Aquarius, Pisces", "IAU names"),
    ("| Ori |", True, "IAU abbreviation of Orion"),
    ("| UMa |", True, "IAU abbreviation of Ursa Major"),
    ("| UMi |", True, "IAU abbreviation of Ursa Minor"),
    ("| Cas |", True, "IAU abbreviation of Cassiopeia"),
    ("| Lyr |", True, "IAU abbreviation of Lyra"),
    ("| And |", True, "IAU abbreviation of Andromeda"),
])

C.finish("BEACD")
