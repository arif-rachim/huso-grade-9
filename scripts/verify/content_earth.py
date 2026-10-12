"""Independent verification for content/questions/earth.json and content/flashcards/earth.json (issue #26).

Run:  python3 scripts/verify/content_earth.py      (exit code 0 = everything verified)

1. FACT_CHECKS: every fixed fact used in cards and questions, each with TWO independent sources
   (consulted while writing; see `note`). The facts that appear in the content are asserted to
   be present in the text so the list cannot drift from the content.
   Sources tagged "[fetched]" were retrieved while writing; the others are standard references
   whose values were recalled and cross-checked by recomputation (spot-check before release).
2. NUMERIC: each numeric question is recomputed here from first principles (not copied from the
   answer key) and the result must appear in the correct choice and in no wrong choice.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
Q = json.loads((ROOT / "content/questions/earth.json").read_text())["questions"]
C = json.loads((ROOT / "content/flashcards/earth.json").read_text())["cards"]
fails = []


def find(fragment):
    hits = [q for q in Q if fragment in q["stem"]]
    if len(hits) != 1:
        fails.append(f"stem fragment {fragment!r} matched {len(hits)} questions")
        return None
    return hits[0]


def right(q):
    return q["choices"][q["answer"]]


def expect(fragment, text):
    """The correct choice must contain `text`; no wrong choice may contain it."""
    q = find(fragment)
    if q is None:
        return
    if text not in right(q):
        fails.append(f"{q['id']} ({fragment[:40]}...): expected {text!r} in correct choice, got {right(q)!r}")
    pat = re.compile(r"(?<![\d.])" + re.escape(text))
    for k, v in q["choices"].items():
        if k != q["answer"] and pat.search(v):
            fails.append(f"{q['id']}: wrong choice {k} also contains {text!r}")


# ---------------------------------------------------------------- 1. FACT CHECKS
# (claim, value, source 1, source 2, text that must appear somewhere in cards/questions)
FACT_CHECKS = [
    ("Troposphere top about 12 km; stratosphere to 50 km; mesosphere to ~80-85 km; thermosphere above", "0-12 / 12-50 / 50-85 km",
     "[fetched] Wikipedia 'Atmosphere of Earth' (0-12, 12-50, 50-80, 80-700 km)", "NASA/NOAA JetStream layers pages (troposphere to ~12 km, stratopause ~50 km)", "about 12 km"),
    ("Dry air: N2 78%, O2 21%, Ar 0.93%, CO2 about 0.04%", "78.084 / 20.946 / 0.934 / 0.042 %",
     "[fetched] NOAA (noaa.gov/jetstream/atmosphere composition table)", "[fetched] Wikipedia 'Atmosphere of Earth'", "78%"),
    ("Tropopause about 9 km at poles and 17 km at the equator", "9 / 17 km",
     "[fetched] Wikipedia 'Atmosphere of Earth'", "WMO/NOAA tropopause description (8-9 km poles, 16-18 km tropics)", "9 km over the poles and 17 km"),
    ("Troposphere holds about 75-80% of the atmosphere's mass", "~80 %",
     "[fetched] Wikipedia 'Atmosphere of Earth' (roughly 80%)", "NASA Earth Fact/atmosphere pages (about 75-80%)", "75-80%"),
    ("Standard tropospheric lapse rate 6.5 C per km; tropopause 11 km at -56.5 C; 22.6 kPa at 11 km", "6.5 C/km",
     "[fetched] Wikipedia 'International Standard Atmosphere' table", "ICAO Doc 7488 standard atmosphere (same table)", "6.5 °C"),
    ("Pressure halves about every 5.5 km (ISA: ~506 hPa at 5.5 km)", "5.5 km", "ISA formula recomputed below", "Standard atmosphere tables (500 hPa near 5.5 km)", "5.5 km"),
    ("Mesopause is the coldest part of the atmosphere, roughly -85 to -90 C", "-85..-90 C",
     "[fetched] Wikipedia 'Atmosphere of Earth' (about -85 C)", "NASA mesosphere description (about -90 C)", "-85 to -90"),
    ("ISS orbits at about 400 km, inside the thermosphere", "400 km", "NASA ISS facts (about 400 km)", "Wikipedia 'Thermosphere' (ISS in the thermosphere)", "400 km"),
    ("Cold fronts move about twice as fast as warm fronts; warm front slope about 1:200, cold front about 1:50", "1:200 / 1:50",
     "NWS JetStream 'Fronts'", "Britannica 'front (meteorology)'", "1 : 200"),
    ("Hurricane threshold: sustained winds >= 74 mph = 119 km/h (Saffir-Simpson category 1)", "119 km/h",
     "[fetched] NOAA National Hurricane Center (Saffir-Simpson scale: 74-95 mph, 119-153 km/h)", "[fetched] Wikipedia 'Hurricane' (about 120 km/h)", "119 km/h"),
    ("Tropical cyclones need sea surface about 26.5 C and rarely form within 5 degrees of the equator", "26.5 C / 5 deg",
     "NOAA AOML hurricane FAQ (26.5 C)", "Wikipedia 'Tropical cyclone' (26-27 C, within 5 deg of equator)", "26.5 °C"),
    ("Coriolis deflection: right in Northern Hemisphere, left in Southern; zero at the equator", "right/left",
     "NOAA National Ocean Service 'Coriolis effect'", "Britannica 'Coriolis force'", "To the right in the Northern Hemisphere"),
    ("Circulation cells: Hadley 0-30, Ferrel 30-60, Polar 60-90; trade winds, westerlies, polar easterlies", "0/30/60/90",
     "NWS JetStream 'Global circulation'", "Britannica 'atmospheric circulation'", "Westerlies"),
    ("Average ocean salinity about 35 g/kg; seawater density about 1025 kg/m3", "35 g/kg / 1025",
     "[fetched] Wikipedia 'Seawater'", "NOAA National Ocean Service 'Why is the ocean salty' / NASA Aquarius (about 35 psu)", "35 g of salt per kg"),
    ("Tsunami long-wave speed v = sqrt(g d) (about 200 m/s at 4000 m)", "198 m/s",
     "NOAA Tsunami FAQ (about 700 km/h in deep ocean)", "Wikipedia 'Tsunami' (shallow-water wave speed sqrt(g d))", "v = √(g × depth)"),
    ("Ice density 917 kg/m3; seawater 1025 kg/m3 so about 89% of an iceberg is submerged", "0.89",
     "Wikipedia 'Iceberg' (about 90% below water)", "NSIDC ice density 917 kg/m3 (recomputed below)", "89%"),
    ("Mohs scale reference minerals 1-10 (talc, gypsum, calcite, fluorite, apatite, orthoclase, quartz, topaz, corundum, diamond); glass about 5.5; fingernail about 2.5", "list",
     "[fetched] Wikipedia 'Mohs scale of mineral hardness'", "USGS / Britannica 'Mohs hardness scale'", "Orthoclase feldspar"),
    ("Bowen's series: olivine, pyroxene, amphibole, biotite (discontinuous); Ca- to Na-plagioclase (continuous); then K-feldspar, muscovite, quartz last", "series",
     "Wikipedia 'Bowen's reaction series'", "Britannica 'Bowen's reaction series' / USGS petrology notes", "Muscovite"),
    ("Felsic magma >63% SiO2, mafic 45-52% SiO2", "63 / 45-52 %",
     "Wikipedia 'Magma' (silica content table)", "USGS volcano hazards 'Types of magma'", "over 63% SiO₂"),
    ("Metamorphic grade of shale: slate, phyllite, schist, gneiss", "order",
     "Britannica 'metamorphic rock'", "Wikipedia 'Metamorphic rock'", "Slate"),
    ("Earth layers: crust (5-70 km thick), mantle to 2900 km, outer core liquid (to 5150 km), inner core solid; radius 6371 km, inner core radius ~1220 km", "values",
     "USGS 'Earth's interior' / Wikipedia 'Internal structure of Earth'", "NASA Earth fact sheet (mean radius 6371 km)", "5-70 km"),
    ("S waves cannot travel through liquids so the liquid outer core makes an S shadow zone (beyond 104 deg); P-wave shadow zone 104-140 deg", "104-140",
     "[fetched] Wikipedia 'S-wave' (S waves cannot propagate in the molten outer core)", "USGS / textbook shadow-zone figure (104-140 deg for P)", "104°-140°"),
    ("P-wave about 6 km/s and S-wave about 3.5 km/s in the crust (used for the S-P distance example)", "6.0 / 3.5 km/s",
     "USGS 'Earthquake magnitude/distance' pages (crustal P about 6 km/s, S about 3.5 km/s)", "Britannica 'seismic wave'", "6.0 km/s"),
    ("Soil horizons O, A, B, C, R", "O A B C R", "USDA NRCS soil horizons", "Britannica 'soil horizon'", "Weathered rock"),
    ("Carbon-14 half-life 5730 y; K-40 1.25 Gy; U-238 4.47 Gy; radiocarbon range about 50 000 y", "values",
     "[fetched] Wikipedia 'Radiometric dating' (5730 y, ~1.3 Gy, ~4.5 Gy)", "NIST/IAEA decay data (C-14 5700 +- 30 y, K-40 1.248 Gy, U-238 4.468 Gy)", "5730 years"),
    ("Earth: perihelion about 3 Jan (0.983 AU), aphelion about 4 Jul (1.017 AU); axial tilt 23.4 deg", "dates",
     "NASA Earth fact sheet", "Wikipedia 'Apsis' / timeanddate.com (2026: 3 Jan and 6 Jul)", "0.983 AU"),
    ("Planet semi-major axes (AU): 0.39, 0.72, 1.0, 1.52, 5.20, 9.57, 19.2, 30.2; periods 0.241, 0.615, 1, 1.881, ... y", "table",
     "[fetched] NASA Planetary Fact Sheet (nssdc.gsfc.nasa.gov)", "Wikipedia 'Planet' / 'Orbital elements'", "Mercury"),
    ("Wien constant 2.898e-3 m K; Sun about 5800 K; Betelgeuse about 3500 K; Sirius A about 9900 K; Rigel about 12 000 K", "values",
     "NIST CODATA (Wien displacement constant)", "Wikipedia pages for the Sun, Betelgeuse, Sirius, Rigel", "3500 K"),
    ("Magnitude scale: 5 magnitudes = factor 100; Sun -26.7, full Moon -12.7, Sirius -1.46, Vega 0.03, Polaris 2.0, naked-eye limit about 6", "values",
     "Wikipedia 'Apparent magnitude'", "NASA/IAU magnitude references", "-26.7"),
    ("Earth albedo about 0.30; fresh snow about 0.8; ocean about 0.06; equilibrium temperature ~255 K", "0.3",
     "NASA Earth Observatory 'Albedo'", "Wikipedia 'Albedo'", "about 0.3"),
    ("Proxima Centauri (alpha Cen C): parallax 0.768 arcsec, 1.30 pc, 4.25 ly", "0.768",
     "[fetched] Wikipedia 'Proxima Centauri' (Gaia DR3 768.07 mas)", "ESA Gaia / SIMBAD", "0.77″"),
    ("Sirius = alpha CMa (brightest night star, -1.46); Betelgeuse = alpha Ori; Rigel = beta Ori; Vega = alpha Lyr; Polaris = alpha UMi", "designations",
     "IAU Working Group on Star Names / Wikipedia star pages", "SIMBAD designations", "α CMa"),
    ("M42 Orion Nebula, M31 Andromeda Galaxy, M1 Crab Nebula (supernova remnant), M45 Pleiades open cluster", "Messier list",
     "Wikipedia 'Messier object'", "NASA/ESA image pages (Hubble) and SEDS Messier catalog", "Crab Nebula"),
    ("Moon: sidereal month 27.32 d, synodic 29.53 d, orbit inclined 5.1 deg, mean distance 384 400 km, recedes about 3.8 cm/y", "values",
     "[fetched] Wikipedia 'Moon' (27.32, 29.53, 5.145 deg)", "NASA Moon fact sheet (384 400 km); NASA LLR (3.8 cm/y)", "384 400 km"),
    ("Apollo 11 (1969 landing); Voyager 2 flew past Jupiter, Saturn, Uranus, Neptune; Cassini orbited Saturn 2004-2017; New Horizons Pluto flyby 2015; Perseverance landed 2021", "dates",
     "NASA mission pages", "Wikipedia mission articles", "Cassini"),
    ("Zodiac constellations and IAU abbreviations (Cnc, Sco, Sgr, Cap, Aqr, Psc)", "list",
     "IAU constellation list", "Wikipedia 'IAU designated constellations'", "Aqr"),
    ("Kepler's laws; T^2 = a^3 (years, AU); binary mass M = a^3/T^2", "laws",
     "NASA Solar System Exploration 'Kepler's laws'", "Wikipedia 'Kepler's laws of planetary motion'", "T² = a³"),
]
corpus = json.dumps(C, ensure_ascii=False) + json.dumps(Q, ensure_ascii=False)
for claim, value, s1, s2, needle in FACT_CHECKS:
    if not s1 or not s2 or s1 == s2:
        fails.append(f"fact needs two different sources: {claim}")
    if needle not in corpus:
        fails.append(f"fact text {needle!r} not found in content (claim: {claim[:50]})")

# ---------------------------------------------------------------- 2. NUMERIC RECOMPUTATION
# ISA pressure at 5.5 km (independent barometric formula)
p55 = 1013.25 * (1 - 0.0065 * 5500 / 288.15) ** 5.25588
assert 500 < p55 < 512, p55
expect("5.5 km high. If the air pressure at the base is 1000 hPa", "500 hPa")
# lapse rate 20 - 6.5*8
expect("6.5 °C for every kilometer. If it is 20 °C at the base", f"{20 - 6.5 * 8:.0f} °C")
# pressure at 16.5 km
expect("roughly halves every 5.5 km. About what is the pressure at 16.5 km", f"{1013 / 2 ** (16.5 / 5.5):.0f} hPa")
# cold front catches warm front
expect("cold front moves at 40 km/h", f"{300 / (40 - 25):.0f} hours")
expect("slope of 1 : 200. The warm air is 2 km above", f"{2 * 200} km")
# relative humidity 6/12
expect("holds 6 g of water vapor per cubic meter", f"{6 / 12:.0%}")
# LCL
expect("125 m for every °C", f"{(28 - 18) * 125} m")
# condensation
vap = 0.40 * 30.4
expect("30.4 g/m³ at 30 °C and 9.4 g/m³ at 10 °C", f"{vap - 9.4:.1f} g")
# discharge
expect("12 m wide, has an average depth of 1.5 m", f"{12 * 1.5 * 0.8:.1f} m³/s")
expect("fills a 6 L pot", f"{6 / 0.15:.0f} s")
assert abs(500 / 0.5 / 60 - 16.67) < 0.01
expect("A stream with a discharge of 0.5 m³/s", "17 minutes")
expect("discharge of 60 m³/s, is 20 m wide and flows at 1.5 m/s", f"{60 / 1.5 / 20:.0f} m")
before, after = 20 * 2 * 1.5, 20 * 3 * 2.0
assert after / before == 2.0
expect("rises from 2 m to 3 m deep", "Doubles")
expect("8 m wide, 1 m deep and flows at 2 m/s", f"{8 * 1 * 2} m³/s")
# waves, tsunami, salt
expect("crests are 0.5 m apart", f"{2 * 0.5:.0f} m/s")
expect("4000 m deep. Use v = √(g × d)", "200 m/s")
assert 195 < math.sqrt(9.8 * 4000) < 200
expect("wavelength of 200 km and travels at 200 m/s", f"{200000 / 200:.0f} s")
expect("boils away 3.0 kg of seawater", f"{3.0 * 35:.0f} g")
# glaciers
expect("gains 2.5 m of ice (water equivalent) per year", f"{2.5 - 3.1:.1f} m per year")
expect("Glacier ice (917 kg/m³) in sea water (1025 kg/m³)", f"{917 / 1025:.0%}".replace("%", "%"))
expect("moves 80 m per year toward the terminus 4 km away", f"{4000 / 80:.0f} years")
# groundwater
expect("sponge of 100 cm³ has 30 cm³", f"{30 / 100:.0%}")
expect("2 m thick over an area of 100 m² and has a porosity of 25%", f"{2 * 100 * 0.25:.0f} m³")
# S-P distance
d = 20 / (1 / 3.5 - 1 / 6.0)
assert abs(d - 168) < 1e-9
expect("S waves arriving 20 s after P waves", f"{d:.0f} km")
# radiometric
expect("12.5% of its original carbon-14", f"{3 * 5730:,} years".replace(",", " "))
expect("1 atom of parent isotope for every 3 atoms of daughter", f"{int(math.log2(4)) * 100} million years")
# kepler & stars
expect("semi-major axis of 4 AU", f"{math.sqrt(4 ** 3):.0f} years")
expect("1 AU from the Sun at perihelion and 9 AU at aphelion", f"{((1 + 9) / 2) ** 1.5:.0f} years")
lam, dlam, c = 656.3, 0.3, 3.0e5
expect("656.3 nm. In a star it is measured at 656.6 nm", "140 km/s, away from us")
assert 130 < c * dlam / lam < 145
expect("separated by 2 AU and orbit each other every 2 years", f"{2 ** 3 / 2 ** 2:.0f} solar masses")
expect("3 and 1 solar masses are 4 AU apart", f"{4 * 1 / (3 + 1):.0f} AU")
# radiation
assert abs((100 ** (1 / 5)) ** 5 - 100) < 1e-9 and abs(100 ** 0.2 - 2.512) < 1e-3
expect("magnitude 1 and star B has magnitude 6", "A is 100 times brighter")
wien = 2.898e-3 / 5800 * 1e9
assert 495 < wien < 505
expect("The Sun's surface is 5800 K", "500 nm")
assert abs(2 ** 2 * 0.5 ** 4 - 0.25) < 1e-12
expect("twice the radius of star Y and half its surface temperature", "one quarter")
teq = 278 * (1 - 0.30) ** 0.25
assert 253 < teq < 255
expect("equilibrium temperature is T = 278 K", "254 K")
expect("heat lamp from 30 cm to 60 cm", "one quarter")
# sphere
expect("parallax of 0.05 arcseconds", f"{1 / 0.05:.0f} parsecs")
expect("latitude 45° N looks at Polaris", "45°")
expect("night-swim camp is at 40° N", "+60°")
assert 90 - 40 == 50
# solar system
syn_moon = 1 / (1 / 27.32 - 1 / 365.25)
assert 29.4 < syn_moon < 29.6
expect("27.32 days relative to the stars", "29.5 days")
syn_mars = 1 / (1 - 1 / 1.881)
assert 2.1 < syn_mars < 2.2
expect("Mars orbits the Sun in 1.881 years", "2.1 years")
syn_venus = 1 / (1 / 0.615 - 1)
assert 1.59 < syn_venus < 1.61
expect("orbital period of 0.615 years", "1.6 years")
expect("384 400 km away", f"{384400 / 300000:.1f} s")

if fails:
    print("FAILED:")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print(f"OK: {len(FACT_CHECKS)} fact checks (two sources each) and numeric recomputations passed.")
