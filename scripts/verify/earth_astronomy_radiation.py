"""Independent checks for materi/earth/astronomy-radiation.md.

Wien's law is recovered by numerically maximizing the Planck function; luminosity ratios and magnitude
ratios are computed from the Planck/flux definitions, not from the shortcut powers."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from earth_geosphere_astronomy_helpers import Checker

C = Checker("materi/earth/astronomy-radiation.md")
ok = C.ok
h, c, k, SIGMA = 6.62607e-34, 2.99792458e8, 1.380649e-23, 5.670374e-8


def planck(lam_m, T):
    x = h * c / (lam_m * k * T)
    if x > 700:
        return 0.0
    return 2 * h * c * c / lam_m ** 5 / math.expm1(x)


def peak_nm(T):
    best, bl = 0, 0
    for i in range(50, 20000):
        l = i * 1e-9
        v = planck(l, T)
        if v > best:
            best, bl = v, l
    return bl * 1e9


def total_flux(T):          # integral of pi*B over wavelength
    s, l = 0.0, 20e-9
    while l < 2e-4:
        s += math.pi * planck(l, T) * 2e-9 * (1 if l < 1e-5 else 50)
        l += 2e-9 * (1 if l < 1e-5 else 50)
    return s


# ---- Wien
for T, expect in ((5772, 502), (3000, 966), (10000, 290), (1000, 2898)):
    ok(abs(peak_nm(T) * T / 1e6 - 2.898) < 0.004, (T, peak_nm(T)))
    ok(abs(peak_nm(T) - expect) / expect < 0.01, (T, peak_nm(T)))
ok(abs(peak_nm(310) - 9300) < 100)
# ---- Stefan-Boltzmann
ok(abs(total_flux(5772) / (SIGMA * 5772 ** 4) - 1) < 0.02)
ok(abs(total_flux(2000) / total_flux(1000) - 16) < 0.5)
ok(abs(SIGMA - 5.670e-8) < 1e-11)

# ---- Example 1: R and T doubled
def lum(R, T):
    return 4 * math.pi * R ** 2 * SIGMA * T ** 4
r1 = lum(2, 2) / lum(1, 1)
ok(abs(r1 - 64) < 1e-9)
C.mcq("**Example 1.**", r1, "D")
for letter, val in (("A", 2 * 2 ** 2), ("C", 2 * 2 ** 4), ("B", 2 ** 4), ("E", 2 ** 3 * 2 ** 4)):
    C.opt_is("**Example 1.**", letter, val)

# ---- Example 2: magnitudes
def flux_ratio(m1, m2):
    return 10 ** (-0.4 * (m1 - m2))
fr = flux_ratio(2.0, 7.0)
ok(abs(fr - 100) < 1e-9)
d_ratio = math.sqrt(fr)
ok(abs(d_ratio - 10) < 1e-9)
C.mcq("**Example 2.**", d_ratio, "C")
C.opt_is("**Example 2.**", "E", fr); C.opt_is("**Example 2.**", "B", 5); C.opt_is("**Example 2.**", "A", 2.512, tol=0.02)
C.opt_is("**Example 2.**", "D", 25)
ok(abs(100 ** 0.2 - 2.512) < 0.001)

# ---- Q1
lam = 2.898e6 / 1000
ok(abs(peak_nm(1000) - 2898) < 15 and lam > 700)
C.choice("**1.**", "E", lambda t: t == "Infrared")
# ---- Q2
ok(abs(1000 * (1 - 0.30) - 700) < 1e-9)
C.mcq("**2.**", 700.0, "B")
# ---- Q3
ok(abs(peak_nm(5000) / peak_nm(10000) - 2) < 0.01, "peak at half the wavelength needs double T")
C.choice("**3.**", "D", lambda t: t == "A is 2 times hotter than B")
# ---- Q4
ok(abs(flux_ratio(-1, 4) - 100) < 1e-9)
def q4(t): return t == "100 times brighter"
C.choice("**4.**", "C", q4)
# ---- Q5
ok(abs(1 / 3 ** 2 - 1 / 9) < 1e-15)
C.choice("**5.**", "A", lambda t: t == "1/9 as large")

# ---- facts
S0, A = 1361.0, 0.30
Teq = (S0 * (1 - A) / (4 * SIGMA)) ** 0.25
ok(abs(Teq - 255) < 1, Teq)
ok(abs(288 - Teq - 33) < 1)
ok(abs((S0 * (1 - A) / SIGMA) ** 0.25 / Teq - math.sqrt(2)) < 1e-9, "forgetting the 4 gives sqrt(2) too hot")
# Sun luminosity from R and T
Ls = lum(6.957e8, 5772)
ok(abs(Ls - 3.83e26) / 3.83e26 < 0.01, Ls)
# solar constant from L and 1 AU
ok(abs(Ls / (4 * math.pi * 1.496e11 ** 2) - 1361) < 5)
# distance modulus: Sun m=-26.74 at 1 AU -> M=4.83
d_pc = 1.496e11 / 3.0857e16
M_sun = -26.74 - 5 * math.log10(d_pc / 10)
ok(abs(M_sun - 4.83) < 0.02, M_sun)
C.fact_checks([
    ("**λmax = 2.898 × 10⁶ nm·K ÷ T**", True, "Wien constant 2.898e-3 m K"),
    ("σ = 5.670 × 10⁻⁸ W/m²/K⁴", abs(SIGMA - 5.670e-8) < 1e-11, "CODATA"),
    ("L = 3.83 × 10²⁶ W", abs(Ls - 3.83e26) / 3.83e26 < 0.01, "solar luminosity"),
    ("S = 1361 W/m²", True, "solar constant"),
    ("Sun −26.7, Sirius −1.5", True, "apparent magnitudes"),
    ("**255 K (−18 °C)**", abs(Teq - 255) < 1, "effective temperature of Earth"),
    ("adds about 33 K", True, "greenhouse warming 288 - 255"),
    ("**Earth overall 0.30**", True, "Bond albedo 0.306"),
    ("(5772 K) peaks at 502 nm", abs(peak_nm(5772) - 502) < 3, "Wien"),
    ("27 °C is 300 K", True, "kelvin conversion"),
])
C.finish("EBDCA")
