"""Independent checks for materi/chemistry/inorganic-electron-config.md."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from itertools import product
from chemistry_inorganic_helpers import Checker, Z, config, unpaired

C = Checker("materi/chemistry/inorganic-electron-config.md")
ok = C.ok
LETTER_L = {"s": 0, "p": 1, "d": 2, "f": 3}

def allowed(n, l, m):
    return n >= 1 and 0 <= l <= n - 1 and -l <= m <= l

# brute-force count of orbitals / electrons per shell and subshell (core ideas 1-2)
for n in (1, 2, 3, 4):
    orbitals = sum(1 for l in range(0, 6) for m in range(-6, 7) if allowed(n, l, m))
    ok(orbitals == n * n)
    ok(2 * orbitals == 2 * n * n)
for l, cnt in ((0, 1), (1, 3), (2, 5)):
    ok(sum(1 for m in range(-5, 6) if abs(m) <= l) == cnt == 2 * l + 1)
ok([2 * n * n for n in (1, 2, 3, 4)] == [2, 8, 18, 32])

def ion_config(sym, charge):
    """Remove electrons from the highest n first (then highest l); add to the next free level for anions."""
    occ = dict(config(Z[sym]))
    for _ in range(charge):
        sh = max(occ, key=lambda s: (int(s[0]), "spdf".index(s[1])))
        occ[sh] -= 1
        if occ[sh] == 0:
            del occ[sh]
    return occ

# configurations quoted in the text
ok(config(8) == {"1s": 2, "2s": 2, "2p": 4})
ok(config(16)["3p"] == 4 and config(16)["3s"] == 2)
ok(config(24) == {"1s": 2, "2s": 2, "2p": 6, "3s": 2, "3p": 6, "4s": 1, "3d": 5})
ok(config(29)["4s"] == 1 and config(29)["3d"] == 10)
ok(config(26)["4s"] == 2 and config(26)["3d"] == 6)
ok(unpaired(config(7)) == 3 and unpaired(config(8)) == 2)   # N 2p3, O 2p4
ok(ion_config("Fe", 2)["3d"] == 6 and "4s" not in ion_config("Fe", 2))
ok(ion_config("Fe", 3)["3d"] == 5 and "4s" not in ion_config("Fe", 3))
ok(sum(config(17).values()) + 1 == 18)   # Cl- has 18 electrons = [Ne]3s2 3p6
ok(unpaired(config(11)) == 1 and unpaired(config(17)) == 1)  # odd electrons -> unpaired

# ---- Example 1: Fe3+ unpaired electrons
fe3 = unpaired(ion_config("Fe", 3))
ok(fe3 == 5, fe3)
C.numopt("**Example 1.**", fe3, "E", tol=0.0)
fe2 = unpaired(ion_config("Fe", 2)); fe0 = unpaired(config(26))
ok(fe2 == 4 and fe0 == 4)
# wrong order: remove 3 electrons from 3d first -> 4s2 3d3 -> 3 unpaired; remove 2 from 3d then ... text says "4s2 3d4"
wrong = dict(config(26)); wrong["3d"] -= 3   # wrong order for Fe3+: 4s2 3d3
ok(wrong["3d"] == 3 and wrong["4s"] == 2 and unpaired(wrong) == 3)
C.distract("**Example 1.**", "C", 3, tol=0.0)
C.distract("**Example 1.**", "D", 4, tol=0.0)

# ---- Example 2: not allowed set
sets = {"A": (2, 1, -1), "B": (3, 2, 0), "C": (1, 0, 0), "D": (2, 2, 1), "E": (4, 3, -3)}
bad = [k for k, v in sets.items() if not allowed(*v)]
ok(bad == ["D"], bad)
o = C.options("**Example 2.**")
ok(o["D"] == "(2, 2, 1)" and o["E"] == "(4, 3, −3)")
for k, v in sets.items():
    ok(o[k].replace("−", "-") == str(v), k)
ok(allowed(4, 3, -3) and allowed(4, 3, 3))

# ---- Q1: 2n^2 for n = 3
C.numopt("**1.**", 2 * 3 * 3, "B", tol=0.0)
ok(2 * 2 * 2 == 8 and 2 * 4 * 4 == 32 and 3 * 3 == 9)
# ---- Q2: Pauli
C.textopt("**2.**", "D", "Pauli")
# ---- Q3: 18 electrons
o = C.options("**3.**")
nelec = {"A": Z["Ca"] - 2, "B": Z["Na"] - 1, "C": Z["K"], "D": Z["Ne"], "E": Z["Mg"] - 2}
ok([k for k, v in nelec.items() if v == 18] == ["A"], nelec)
ok(sum(config(18).values()) == 18 and config(18) == {"1s": 2, "2s": 2, "2p": 6, "3s": 2, "3p": 6})
C.textopt("**3.**", "A", "Ca²⁺")
# ---- Q4: paramagnetic
species = {"A": ("Zn", 0), "B": ("Mg", 2), "C": ("Cu", 1), "D": ("Ar", 0), "E": ("Ti", 2)}
para = [k for k, (s, q) in species.items() if unpaired(ion_config(s, q)) > 0]
ok(para == ["E"], para)
ok(unpaired(ion_config("Ti", 2)) == 2 and ion_config("Ti", 2) == {**{k: v for k, v in config(22).items() if k != "4s" and k != "3d"}, "3d": 2})
ok(ion_config("Cu", 1) == {**{k: v for k, v in config(29).items() if k not in ("4s", "3d")}, "3d": 10})
C.textopt("**4.**", "E", "Ti²⁺")
# ---- Q5: 3p orbital
sets5 = {"A": (3, 0, 0), "B": (3, 2, 1), "C": (3, 1, -1), "D": (2, 1, 0), "E": (3, 1, 2)}
three_p = [k for k, v in sets5.items() if allowed(*v) and v[0] == 3 and v[1] == 1]
ok(three_p == ["C"], three_p)
ok(not allowed(*sets5["E"]))
o = C.options("**5.**")
for k, v in sets5.items():
    ok(o[k].replace("−", "-") == str(v), k)
ok(C.key_letter(5) == "C")
C.done()
