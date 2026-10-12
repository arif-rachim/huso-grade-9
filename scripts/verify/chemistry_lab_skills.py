"""Independent checks for materi/chemistry/lab-skills.md.
Method: the targets are re-measured from the dots inside lab-accuracy-precision.svg; uncertainties are propagated by trying every
corner of the +/- ranges; titration errors are simulated; significant figures are applied with the decimal module."""
import itertools, math, re, sys, pathlib
from decimal import Decimal, ROUND_HALF_UP
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk, ROOT, parse

C = Chk("materi/chemistry/lab-skills.md")
ok = C.ok

# ---- the targets in the picture really show what their captions say
svg = (ROOT / "public/content/chemistry/lab-accuracy-precision.svg").read_text()
CENTER = {"A": (125, 100), "B": (375, 100), "C": (125, 272), "D": (375, 272)}
stats = {}
for key in "ABCD":
    grp = re.search(rf'<g id="target-{key}">(.*?)</g>', svg, re.S).group(1)
    dots = [(float(x), float(y)) for x, y, r in re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="(3\.6)"', grp)]
    ok(len(dots) == 6, (key, len(dots)))
    mx, my = sum(d[0] for d in dots) / 6, sum(d[1] for d in dots) / 6
    bias = math.hypot(mx - CENTER[key][0], my - CENTER[key][1])
    spread = sum(math.hypot(d[0] - mx, d[1] - my) for d in dots) / 6
    stats[key] = (bias, spread)
precise = {k: v[1] < 16 for k, v in stats.items()}
accurate = {k: v[0] < 12 for k, v in stats.items()}
ok(precise == {"A": True, "B": True, "C": False, "D": False}, stats)
ok(accurate == {"A": True, "B": False, "C": True, "D": False}, stats)

# ---- Example 1: mass for 250.0 mL of 0.100 M NaCl, then judge each plan
M_NACL = 22.99 + 35.45
need = 0.100 * 0.2500 * M_NACL
ok(abs(need - 1.461) < 0.001, need)
o = C.options("**Example 1.**")
plans = {}
for k, t in o.items():
    mass = float(re.match(r"([\d.]+) g", t).group(1))
    vol_flask = "250.0 mL volumetric flask" in t
    transfers = "transferred and rinsed" in t
    plans[k] = (abs(mass - need) / need < 0.005 and vol_flask and transfers)
ok([k for k, v in plans.items() if v] == ["B"], plans)
ok(abs(14.61 / need - 10) < 0.01 and abs(5.844 / need - 4) < 0.01)      # D is 10x, E is 4x (the mass for 1 L)
ok("**Answer: (B).**" in C.txt.split("**Example 1.**")[1].split("**Example 2.**")[0])

# ---- Example 2: propagate by trying every corner of the +/- box
m0, dm, v0, dv = 15.62, 0.01, 5.8, 0.1
vals = [(m0 + a * dm) / (v0 + b * dv) for a, b in itertools.product((-1, 1), repeat=2)]
half_range = (max(vals) - min(vals)) / 2
rho = m0 / v0
ok(abs(rho - 2.693) < 0.001 and abs(half_range - 0.048) < 0.002, (rho, half_range))
rel_sum = dm / m0 + dv / v0
ok(abs(rho * rel_sum - 0.048) < 0.001 and abs(rel_sum - 0.0179) < 0.0001)
o2 = C.options("**Example 2.**")
unc = {k: float(re.search(r"± ([\d.]+)", t).group(1)) for k, t in o2.items()}
ok(min(unc, key=lambda k: abs(unc[k] - half_range)) == "B" and unc["B"] == 0.05, unc)
ok(unc["C"] == round(dm + dv, 2) and unc["D"] == 0.10 and unc["A"] == 0.01 and unc["E"] == 0.02)

# ---- Q1: tight group, off target => precise, not accurate (target B of the picture), systematic
ok(precise["B"] and not accurate["B"])
ok(C.options("**1.**")["C"].startswith("precise but not accurate") and C.key_letter(1) == "C")

# ---- Q2: titration simulation with the air bubble: reading counts the bubble volume as delivered titrant
c_base, v_acid, c_acid_true = 0.100, 25.00, 0.100
v_true = c_acid_true * v_acid / c_base            # volume of base really needed
bubble = 0.05
v_read = v_true + bubble                           # reading includes the air space that filled with liquid
c_calc = c_base * v_read / v_acid
ok(c_calc > c_acid_true)
# other errors of the lesson, same model
c_diluted = 0.095                                   # titrant diluted by water in the buret
v_needed = c_acid_true * v_acid / c_diluted
ok(c_base * v_needed / v_acid > c_acid_true)         # nominal 0.100 M used in the calculation -> too high
n_acid_diluted = c_acid_true * (v_acid * 0.98) / 1  # sample diluted by water in the pipette: fewer moles delivered
ok(c_base * (n_acid_diluted / c_base) / v_acid < c_acid_true)   # too low
wet_flask = c_base * (c_acid_true * v_acid / c_base) / v_acid      # water in the flask: same moles, same volume of base
ok(abs(wet_flask - c_acid_true) < 1e-12)
ok(C.options("**2.**")["A"] == "too high" and C.key_letter(2) == "A")

# ---- Q3: which apparatus does the job
JOB = {"Büchner funnel": "solid from liquid", "condenser": "turn vapor to liquid", "buret": "deliver liquid", "crucible": "heat solids strongly",
       "separatory funnel": "separate immiscible liquids"}
o3 = C.options("**3.**")
ok([k for k, v in o3.items() if JOB[v] == "separate immiscible liquids"] == ["E"] and C.key_letter(3) == "E")
rf = 3.6 / 8.0
ok(abs(rf - 0.45) < 1e-12 and 0 <= rf <= 1)

# ---- Q4: percent error
err = abs(98.6 - 100.0) / 100.0 * 100
ok(abs(err - 1.4) < 1e-9)
C.opt2("**4.**", "B", err)
C.opt2("**4.**", "C", err * 10)
C.opt2("**4.**", "A", err / 100)
ok(C.options("**4.**")["E"] == "1.4 °C" and C.key_letter(4) == "B")

# ---- Q5: addition by decimal places
vals5 = [Decimal("12.11"), Decimal("0.3"), Decimal("1.457")]
total = sum(vals5)
places = min(-v.as_tuple().exponent for v in vals5)
ok(total == Decimal("13.867") and places == 1)
res = total.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
ok(res == Decimal("13.9"))
C.opt2("**5.**", "D", float(res))
ok(C.key_letter(5) == "D")
ok(float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) == 13.87)   # the wrong-rule answer (B)
C.letters_spread()
C.done()
