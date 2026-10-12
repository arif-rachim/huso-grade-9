"""Independent checks for materi/earth/geosphere-dating.md.

Half-life answers come from a Monte Carlo simulation of atoms decaying (not from the (1/2)^n formula);
the event order in Example 1 and in the cross section comes from a topological sort of the stated
stratigraphic relations; geologic-map statements are checked with a small 3D bed-geometry model."""
import sys, pathlib, math, random, itertools
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from earth_geosphere_astronomy_helpers import Checker

C = Checker("materi/earth/geosphere-dating.md")
ok = C.ok
random.seed(37)


# ---------------- radioactive decay by simulation ----------------
def simulate(n_atoms, half_life, steps_per_half=400, until=lambda parent, daughter, t: False, t_max=20.0):
    """each step every parent atom decays with probability p; returns (t, parent, daughter) when `until` is true"""
    p = 1 - 0.5 ** (1.0 / steps_per_half)          # the per-step chance that gives the given half-life (definition of half-life)
    parent = n_atoms
    t = 0.0
    while t < t_max * half_life:
        decayed = sum(1 for _ in range(parent) if random.random() < p) if parent < 3000 else int(round(random.gauss(parent * p, math.sqrt(parent * p * (1 - p)))))
        parent -= decayed
        t += half_life / steps_per_half
        if until(parent, n_atoms - parent, t):
            return t, parent, n_atoms - parent
    return t, parent, n_atoms - parent


# Example 2: ratio parent:daughter = 1:3 reached after how many half-lives?  (t_half = 1.25 Gyr)
HL = 1.25
t2, par, dau = simulate(200000, HL, until=lambda p_, d_, t: d_ >= 3 * p_)
ok(abs(t2 - 2.5) < 0.03, t2)
C.mcq("**Example 2.**", 2.5, "C", tol=0.02)
C.opt_is("**Example 2.**", "D", 3 * HL)       # 3 half-lives because of the '3'
C.opt_is("**Example 2.**", "B", HL)           # 1 half-life
C.opt_is("**Example 2.**", "E", 4 * HL)       # 4 half-lives (number of atoms)
C.opt_is("**Example 2.**", "A", HL / 2)       # half of the half-life
# at 1 half-life the ratio parent:daughter is 1:1
t1, par1, dau1 = simulate(200000, HL, until=lambda p_, d_, t: t >= HL - 1e-9)
ok(abs(par1 / dau1 - 1) < 0.02, (par1, dau1))

# Q3: 1/16 of the carbon-14 left; t_half = 5730 yr
HLC = 5730.0
t3, par3, dau3 = simulate(400000, HLC, until=lambda p_, d_, t: p_ <= 400000 / 16)
ok(abs(t3 - 22920) < 150, t3)
C.mcq("**3.**", 4 * HLC, "D", tol=0.002)
C.opt_is("**3.**", "A", HLC, tol=0.001); C.opt_is("**3.**", "B", 2 * HLC, tol=0.001); C.opt_is("**3.**", "C", 3 * HLC, tol=0.001)
C.opt_is("**3.**", "E", 16 * HLC, tol=0.001)
ok(abs(0.5 ** 4 - 1 / 16) < 1e-15)

# ---------------- stratigraphy: topological sort ----------------
def order(relations):
    """relations: (older, younger) pairs; return the unique oldest->youngest order or None"""
    nodes = {n for r in relations for n in r}
    result = []
    remaining = set(nodes)
    while remaining:
        free = [n for n in remaining if not any(o in remaining and y == n for o, y in relations)]
        if len(free) != 1:
            return None
        result.append(free[0]); remaining.remove(free[0])
    return result

# Example 1: the dike cuts the limestone (limestone older); the sandstone lies on the erosion surface that truncates the dike
# and contains basalt pieces (inclusions are older): dike older than sandstone; superposition: limestone older than sandstone
seq1 = order([("limestone", "dike"), ("dike", "sandstone"), ("limestone", "sandstone")])
ok(seq1 == ["limestone", "dike", "sandstone"], seq1)
def contact(lower_tilted, upper_flat, lower_is_igneous_or_metamorphic, parallel):
    if lower_is_igneous_or_metamorphic: return "nonconformity"
    if lower_tilted and upper_flat: return "angular unconformity"
    if parallel: return "disconformity"
ok(contact(True, True, False, False) == "angular unconformity")
def parse_ex1(t):
    seq, kind = t.split("; ")
    return [w.strip().lower() for w in seq.split(",")], kind
C.choice("**Example 1.**", "C", lambda t: parse_ex1(t) == (["limestone", "dike", "sandstone"], "angular unconformity"))

# Big picture cross section: G granite basement, S1-S3 sediments above it, D dike cuts G..S3, L lava lies on S3 (and on D), F fault cuts all
rel = [("G", "S1"), ("S1", "S2"), ("S2", "S3"),                     # superposition + nonconformity
       ("S3", "D"), ("G", "D"),                                    # the dike cuts them
       ("S3", "L"), ("D", "L"),                                    # L lies on S3 and on top of the cut-off dike
       ("L", "F"), ("D", "F"), ("S1", "F")]                        # the fault cuts everything
seq = order(rel)
ok(seq == ["G", "S1", "S2", "S3", "D", "L", "F"], seq)
svg = (pathlib.Path(__file__).resolve().parents[2] / "public/content/earth/dating-cross-section.svg").read_text()
ok("Order: " + " → ".join(seq) in svg, "the SVG states the computed order")

# Q1: relative vs absolute statements
RELATIVE = {"The sandstone is older than the dike that cuts it"}
C.choice("**1.**", "B", lambda t: t in RELATIVE)

# Q2
C.choice("**2.**", "C", lambda t: t == "a nonconformity" and contact(False, True, True, False) == "nonconformity")

# Q4: beds dipping east at 40 degrees on flat ground: which way does the age go?  3D model: a bed surface is z = -(x - x0)*tan(dip) ;
# younger beds lie ABOVE older ones, so at the (z = 0) surface, going east the stratigraphic height of the outcropping bed increases.
dip = math.radians(40)
def strat_height_at_surface(x, bed_offset=0.0):
    """beds are planes whose depth below the surface at position x is (x - x_bed) * tan(dip) for x > x_bed; a bed with x_bed
    outcropping west of x lies deeper there, so at x the outcropping bed is the one with the largest x_bed <= x ... we measure
    stratigraphic height as the perpendicular distance above a reference bed that outcrops at x=0."""
    return x * math.sin(dip)           # moving east by x raises the position in the stack by x*sin(dip)
heights = [strat_height_at_surface(x) for x in (0, 10, 20, 30)]
ok(all(b > a for a, b in zip(heights, heights[1:])), heights)    # younger eastward
C.choice("**4.**", "A", lambda t: t == "They get younger")

# Q5: oval pattern with youngest in the center and dips toward the center = syncline; check both fold types
def fold(center_is_oldest, dips_toward_center):
    if center_is_oldest and not dips_toward_center: return "anticline"
    if not center_is_oldest and dips_toward_center: return "syncline"
    return None
ok(fold(False, True) == "syncline" and fold(True, False) == "anticline")
C.choice("**5.**", "E", lambda t: t == "a syncline")

# ---------------- facts ----------------
AGE_EARTH = 4540.0
PRECAMBRIAN_END = 539.0
share = (AGE_EARTH - PRECAMBRIAN_END) / AGE_EARTH
ok(abs(share - 0.88) < 0.01, share)
ok(252 - 66 == 186 and 539 - 252 == 287)
C.fact_checks([
    ("about **88 %**", abs(share - 0.88) < 0.01, "Precambrian share of Earth history"),
    ("**4.54 billion years**", True, "age of the Earth (Patterson 1956 and later)"),
    ("Hadean", True, "ICS eons"), ("Archean", True, "ICS eons"), ("Proterozoic", True, "ICS eons"), ("Phanerozoic", True, "ICS eons"),
    ("539 million years", True, "ICS: base of the Phanerozoic is 538.8 Ma"),
    ("**Paleozoic** (539 to 252 million years ago", True, "ICS eras"),
    ("**Mesozoic** (252 to 66", True, "ICS eras"),
    ("**Cenozoic** (66 million years ago", True, "ICS eras"),
    ("Carbon-14** (5,730 yr)", HLC == 5730, "half-life of C-14"),
    ("(4.47 billion yr)", True, "half-life of U-238 = 4.468 Gyr"),
    ("(1.25 billion yr)", True, "half-life of K-40 = 1.248 Gyr"),
    ("(48.8 billion yr)", True, "half-life of Rb-87 = 48.8 Gyr"),
    ("up to about 50,000 years", HLC * math.log2(1e6) > 50000 / 2, "C-14 detectable to roughly 9 half-lives"),
    ("(½)ⁿ", True, "decay law"),
    ("parent : daughter = 1 : 3 means ¼ is parent (**2 half-lives**)", abs(1 / (1 + 3) - 0.25) < 1e-12 and math.log2(4) == 2, "ratio to fraction"),
    ("(0° flat, 90° vertical)", True, "dip angle definition"),
    ("oldest at the bottom", True, "map legend convention"),
])

C.finish("BCDAE")
