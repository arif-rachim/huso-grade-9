"""Independent checks for materi/chemistry/lembar-ringkas.md (the cheat sheet): every number or rule that can be recomputed is.
Method: constants converted from first principles, quantum-number counting by enumeration, the Madelung rule generated from (n + l, n),
Kf and Kb recomputed from the molar enthalpies, weak-acid shortcut compared with the exact quadratic, VSEPR angles from vectors."""
import itertools, math, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_p2_helpers import Chk, ROOT

C = Chk("materi/chemistry/lembar-ringkas.md")
ok = C.ok
T = C.txt

# ---- constants and quick numbers
R = 8.314
ok(abs(R / 101.325 - 0.08206) < 0.00001)                       # J -> L atm
ok(abs(R * 273.15 / 101.325 - 22.414) < 0.01)                  # molar volume
ok("22.4 L/mol" in T and "0.08206" in T and "96 485" in T and "6.626 × 10⁻³⁴" in T and "2.998 × 10⁸" in T)
ok(abs(6.022e23 * 1.602e-19 - 96485) < 20)                     # F = N_A e
ok("4.184" in T)

# ---- pH and acids
Ka, c = 1.8e-5, 0.10
approx = math.sqrt(Ka * c)
exact = (-Ka + math.sqrt(Ka * Ka + 4 * Ka * c)) / 2
ok(abs(approx - exact) / exact < 0.01, (approx, exact))         # x << c: shortcut good to 1 %
Kw = 1e-14
ok(abs(Ka * (Kw / Ka) - Kw) < 1e-25)                            # Ka * Kb = Kw
pKa = -math.log10(Ka)
ok(abs(pKa + (-math.log10(Kw / Ka)) - 14) < 1e-9)
# Henderson-Hasselbalch against the exact equilibrium for a buffer
HA, A = 0.20, 0.10
h = Ka * HA / A
ok(abs(-math.log10(h) - (pKa + math.log10(A / HA))) < 1e-9)
# Ksp: s = cube root(Ksp/4) for A2B and AB2
s0 = 0.011
Ksp = s0 * (2 * s0) ** 2                                         # Ca(OH)2-type: [M][OH]^2 = s (2s)^2 = 4 s^3
ok(abs((Ksp / 4) ** (1 / 3) - s0) < 1e-12)
ok(abs(math.sqrt(1.8e-10) - 1.34e-5) < 1e-7)                     # AgCl: s = sqrt(Ksp)
# ranges of the indicators agree with the quantitative file
Q = (ROOT / "materi/chemistry/analytical-quantitative.md").read_text()
for rng in ("3.1–4.4", "6.0–7.6", "8.2–10.0"):
    ok(rng in Q)
ok("methyl orange 3.1–4.4" in T and "bromothymol blue 6.0–7.6" in T and "phenolphthalein 8.2–10" in T)

# ---- equilibrium, energy, colligative
ok(abs(R * 298.15 * math.log(10) / 1000 - 5.708) < 0.01)         # the 5.7 kJ shortcut in the equilibrium file
Kf = R * 273.15 ** 2 * 18.015 / (1000 * 6010)
Kb = R * 373.15 ** 2 * 18.015 / (1000 * 40700)
ok(abs(Kf - 1.86) < 0.01 and abs(Kb - 0.512) < 0.002, (Kf, Kb))
ok("0.512" in T and "1.86" in T and "6.01" in T and "40.7" in T)
ok(abs(-2 * 96485 * 1.10 / 1000 + 212.3) < 0.1)                  # dG = -nFE for the Daniell cell, about -212 kJ
ok(abs(math.log(2) - 0.693) < 0.0005)                            # t1/2 = 0.693 / k
ok(abs(6.626e-34 * 2.998e8 / 500e-9 - 3.97e-19) < 0.01e-19)     # E = hc / lambda, 500 nm
# the four sign cases of dG = dH - T dS
def spont(dH, dS, Tk):
    return dH - Tk * dS < 0
ok(spont(-1, +1, 300) and spont(-1, +1, 3000))                   # (-, +) always
ok(not spont(+1, -1, 300) and not spont(+1, -1, 3000))           # (+, -) never
ok(spont(-100, -0.1, 300) and not spont(-100, -0.1, 3000))       # (-, -) only at low T
ok(not spont(100, 0.1, 300) and spont(100, 0.1, 3000))           # (+, +) only at high T

# ---- atoms
for n in range(1, 5):
    states = [(n, l, m, s) for l in range(n) for m in range(-l, l + 1) for s in (+0.5, -0.5)]
    ok(len(states) == 2 * n * n)
orb = sorted(((n, l) for n in range(1, 8) for l in range(0, min(n, 4))), key=lambda t: (t[0] + t[1], t[0]))
seq = " ".join(f"{n}{'spdf'[l]}" for n, l in orb)
ok(seq.startswith("1s 2s 2p 3s 3p 4s 3d 4p 5s 4d 5p 6s"), seq)
ok("1s 2s 2p 3s 3p **4s 3d** 4p 5s 4d 5p 6s" in T)
ok(18 + 1 + 5 == 24 and 18 + 1 + 10 == 29)                      # Cr and Cu electron counts
# decay bookkeeping
A, Z = 226, 88                                                    # Ra-226 -> Rn-222 + He-4
ok((A - 4, Z - 2) == (222, 86))
ok((14, 6 + 1) == (14, 7))                                        # C-14 -> N-14 + e-
ok(abs(0.5 ** 3 - 1 / 8) < 1e-12)

# ---- VSEPR angles from vectors
def angle(v, w):
    d = sum(a * b for a, b in zip(v, w))
    return math.degrees(math.acos(d / (math.sqrt(sum(a * a for a in v)) * math.sqrt(sum(a * a for a in w)))))
tet = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
ok(all(abs(angle(a, b) - 109.47) < 0.01 for a, b in itertools.combinations(tet, 2)))
oct_ = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
ok({round(angle(a, b)) for a, b in itertools.combinations(oct_, 2)} == {90, 180})
trig = [(math.cos(math.radians(k * 120)), math.sin(math.radians(k * 120)), 0) for k in range(3)]
ok(all(abs(angle(a, b) - 120) < 1e-9 for a, b in itertools.combinations(trig, 2)))
for must in ("109.5° / ≈ 107° / ≈ 104.5°", "sp³d²", "square planar", "seesaw", "T-shaped", "XeF₂", "BrF₅"):
    ok(must in T, must)

# ---- consistency with the other files of the subject
Fl = (ROOT / "materi/chemistry/analytical-qualitative.md").read_text()
for w in ("crimson", "intense yellow", "lilac", "orange-red", "scarlet", "apple green", "blue-green"):
    ok(w in Fl and w in T, w)
Fg = (ROOT / "materi/chemistry/organic-functional-groups.md").read_text()
ok("carboxylic acid (≈ 5) > phenol (≈ 10) > water ≈ alcohol (≈ 16) > ketone α-H (≈ 19) > terminal alkyne (25) > amine N–H (≈ 35)" in Fg)
ok("carboxylic acid ≈ 5 · phenol 10 · water, alcohol ≈ 16 · ketone α-H ≈ 19 · terminal alkyne 25 · amine N–H ≈ 35 · alkane ≈ 50" in T)
ok("ΔH°rxn = Σ ΔHf°(products) − Σ ΔHf°(reactants)" in T)
# degree of unsaturation example (benzene C6H6 = 4)
ok((2 * 6 + 2 - 6) / 2 == 4)
# percent error example from the lab file
ok(abs(abs(98.6 - 100.0) / 100.0 * 100 - 1.4) < 1e-9)
# length: two printable pages
ok(T.count("## 📄 Page") == 2)
print(f"OK {C.n} checks")
