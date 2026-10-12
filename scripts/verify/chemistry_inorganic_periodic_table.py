"""Independent checks for materi/chemistry/inorganic-periodic-table.md."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from math import lcm
from chemistry_inorganic_helpers import Checker, Z, config, group_period

C = Checker("materi/chemistry/inorganic-periodic-table.md")
ok = C.ok

# ---- FACT_CHECKS (reference data written from the standard tables; used to decide the answers)
MP_BP = {  # element: (melting point, boiling point) in deg C at 1 atm
    "Cl2": (-101.5, -34.0), "Br2": (-7.2, 58.8), "I2": (113.7, 184.3), "Ne": (-248.6, -246.1), "S": (115.2, 444.7),
    "Hg": (-38.8, 356.7)}
def state(x, t=20.0):
    mp, bp = MP_BP[x]
    return "solid" if t < mp else ("liquid" if t < bp else "gas")
ok(state("Br2") == "liquid" and state("Hg") == "liquid")
ok(all(state(x) != "liquid" for x in ("Cl2", "I2", "Ne", "S")))
ok(state("Cl2") == "gas" and state("Ne") == "gas" and state("I2") == "solid" and state("S") == "solid")

# ---- Example 1: Z = 34
per, grp = group_period(34)
occ = config(34)
shells = {}
for sh, e in occ.items():
    shells[int(sh[0])] = shells.get(int(sh[0]), 0) + e
ok([shells[k] for k in sorted(shells)] == [2, 8, 18, 6], shells)
ok((per, grp) == (4, 16) and 2 + 8 + 18 + 6 == 34, (per, grp))
C.textopt("**Example 1.**", "C", "Period 4, group 16")
o = C.options("**Example 1.**")
ok(group_period(Z["Cr"]) == (4, 6), "Cr is period 4 group 6 (trap B)")
ok(o["B"] == "Period 4, group 6" and o["A"] == "Period 3, group 16" and o["D"] == "Period 6, group 4" and o["E"] == "Period 4, group 14")
ok(group_period(Z["Si"])[1] == 14 and group_period(Z["Ge"]) == (4, 14))
ok(C.key_text(1) is not None)  # key exists

# ---- Example 2: same group
sets = {"A": (6, 7, 8), "B": (9, 17, 35), "C": (10, 11, 12), "D": (2, 10, 20), "E": (1, 2, 3)}
same = [k for k, zs in sets.items() if len({group_period(z)[1] for z in zs}) == 1]
ok(same == ["B"], same)
ok([C.options("**Example 2.**")[k] for k in "ABCDE"] == [", ".join(map(str, sets[k])) for k in "ABCDE"])
ok(group_period(2)[1] == 18 and group_period(10)[1] == 18 and group_period(20)[1] == 2)
ok(len({group_period(z)[0] for z in sets["A"]}) == 1)
ok(len({group_period(z)[0] for z in sets["C"]}) > 1 and len({group_period(z)[0] for z in sets["E"]}) > 1)
ok(sum(config(2).values()) == 2)  # helium has 2 valence electrons

# ---- Core ideas: valence electrons = group (1,2) or group-10 (13-18); quick-check sulfur
def valence(z):
    p, g = group_period(z)
    occ = config(z)
    return occ.get(f"{p}s", 0) + occ.get(f"{p}p", 0)
ok(valence(Z["S"]) == 6 and group_period(Z["S"]) == (3, 16))
for sym in ("Li", "Na", "K"):
    ok(valence(Z[sym]) == 1 and group_period(Z[sym])[1] == 1)
for sym in ("Be", "Mg", "Ca"):
    ok(valence(Z[sym]) == 2)
for sym in ("B", "Al", "Ga", "N", "P", "O", "S", "F", "Cl", "Br"):
    g = group_period(Z[sym])[1]
    ok(valence(Z[sym]) == g - 10, sym)
ok([group_period(Z[s])[1] for s in ("Ti", "Fe", "Cu", "Zn", "Mn")] == [4, 8, 11, 12, 7])

# ---- Q1 bromine liquid
C.textopt("**1.**", "C", "Bromine")
# ---- Q2 Li, Na, K
ok([valence(Z[s]) for s in ("Li", "Na", "K")] == [1, 1, 1])
ok(len({Z[s] for s in ("Li", "Na", "K")}) == 3, "different protons")
ok(len({group_period(Z[s])[0] for s in ("Li", "Na", "K")}) == 3, "different periods = shells")
C.textopt("**2.**", "A", "One valence electron")
# ---- Q3 Al2O3 via charge balance (brute force)
q_al, q_o = 3, 2
best = min(((a, b) for a in range(1, 6) for b in range(1, 6) if a * q_al == b * q_o), key=lambda ab: ab[0] + ab[1])
ok(best == (2, 3))
o = C.options("**3.**")
ok(o["D"] == "Al₂O₃" and o["A"] == "AlO" and len(o) == 5)
ok(1 * 3 != 1 * 2 and 2 * 3 != 1 * 2 and 1 * 3 != 2 * 2 and 3 * 3 != 2 * 2)  # no other option balances
C.ok(C.key_letter(3) == "D")
ok(group_period(Z["Al"])[1] == 13 and group_period(Z["O"])[1] == 16)
# ---- Q4 text
C.textopt("**4.**", "B", "Fe²⁺", "Fe³⁺")
ok(C.key_letter(4) == "B")
# ---- Q5 d-block
dblock = {s: 21 <= Z[s] <= 30 or 39 <= Z[s] <= 48 for s in ("Ca", "Al", "Sn", "Se", "Ti")}
ok([s for s, v in dblock.items() if v] == ["Ti"])
C.textopt("**5.**", "E", "Ti")
ok(group_period(Z["Ti"])[1] == 4)
C.done()
