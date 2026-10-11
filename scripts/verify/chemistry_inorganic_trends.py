"""Independent checks for materi/chemistry/inorganic-trends.md (data = standard reference values)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry_inorganic_helpers import Checker, Z, config, group_period, unpaired

C = Checker("materi/chemistry/inorganic-trends.md")
ok = C.ok

# ---- FACT_CHECKS: reference data
IE1 = {"Li": 520, "Be": 900, "B": 801, "C": 1086, "N": 1402, "O": 1314, "F": 1681, "Ne": 2081, "Na": 496,
       "Mg": 738, "Al": 578, "K": 419, "Ca": 590, "Rb": 403, "Cs": 376}      # kJ/mol
EN = {"F": 3.98, "O": 3.44, "Cl": 3.16, "N": 3.04, "Br": 2.96, "S": 2.58, "C": 2.55, "Cs": 0.79, "K": 0.82, "Na": 0.93, "Li": 0.98}
RADIUS = {"Mg": 150, "Si": 110, "Cl": 100, "K": 220, "Cs": 260}                          # empirical atomic radii, pm
IONIC = {"O2-": 140, "F-": 133, "Na+": 102, "Mg2+": 72, "Al3+": 54}                      # pm, Shannon CN 6
MG_IE = [738, 1451, 7733, 10543, 13630]
EA = {"F": 328, "Cl": 349}   # kJ/mol released

# core idea 3: dips and trends
ok(IE1["Be"] > IE1["B"] and IE1["N"] > IE1["O"], "dips")
ok(IE1["Li"] < IE1["Be"] and IE1["B"] < IE1["C"] < IE1["N"] < IE1["F"] < IE1["Ne"])
ok(IE1["Li"] > IE1["Na"] > IE1["K"] > IE1["Rb"] > IE1["Cs"], "down the group IE falls")
ok(unpaired(config(7)) == 3 and unpaired(config(8)) == 2)   # N 2p3, O 2p4 has a pair
# core idea 4,5
ok(EA["Cl"] > EA["F"])
ok(max(EN, key=EN.get) == "F" and 3.9 < EN["F"] < 4.1 and EN["O"] > EN["Cl"] > EN["N"])
ok(EN["Li"] > EN["Na"] > EN["K"] > EN["Cs"])
ok(group_period(Z["Cs"]) == (6, 1))

# ---- Example 1: isoelectronic series
ions = {"O2-": ("O", -2), "F-": ("F", -1), "Na+": ("Na", 1), "Mg2+": ("Mg", 2), "Al3+": ("Al", 3)}
elec = {k: Z[s] - q for k, (s, q) in ions.items()}
ok(set(elec.values()) == {10}, elec)
by_protons = sorted(ions, key=lambda k: -Z[ions[k][0]])         # more protons first = smaller
by_data = sorted(ions, key=lambda k: IONIC[k])
ok(by_protons == by_data == ["Al3+", "Mg2+", "Na+", "F-", "O2-"], (by_protons, by_data))
o = C.options("**Example 1.**")
ok(len(o) == 5)
norm = str.maketrans({"²": "2", "³": "3", "⁺": "+", "⁻": "-"})
good = [k for k, v in o.items() if [n.strip().translate(norm) for n in v.split("<")] == by_data]
ok(good == ["B"], good)
ok(o["A"].split(" < ")[::-1] == o["B"].split(" < "), "A is the exact reverse")

# ---- Example 2: successive IEs
ratios = [MG_IE[i + 1] / MG_IE[i] for i in range(4)]
ok([round(r, 1) for r in ratios] == [2.0, 5.3, 1.4, 1.3], [round(r, 2) for r in ratios])
jump = max(range(4), key=lambda i: ratios[i]) + 1      # number of electrons before the jump
ok(jump == 2)
ok(group_period(Z["Mg"]) == (3, 2))
C.textopt("**Example 2.**", "B", "Group 2")
ok(C.options("**Example 2.**")["B"] == "Group 2")

# ---- Q1 largest radius
ok(max(["Mg", "Cl", "K", "Cs", "Si"], key=lambda s: RADIUS[s]) == "Cs")
C.textopt("**1.**", "D", "Cs")
ok(RADIUS["K"] < RADIUS["Cs"] and group_period(Z["Cs"])[0] == 6)
# ---- Q2 highest EN among listed
ok(max(["Cl", "O", "N", "S", "Br"], key=lambda s: EN[s]) == "O")
C.textopt("**2.**", "B", "O")
ok(round(EN["Br"], 1) == 3.0 and round(EN["N"], 1) == 3.0 and round(EN["Cl"], 1) == 3.2 and round(EN["S"], 1) == 2.6)
# ---- Q3 fastest with water (lowest IE among options)
ok(min(["Li", "Na", "K", "Mg", "Ca"], key=lambda s: IE1[s]) == "K")
C.textopt("**3.**", "C", "Potassium")
ok(min(IE1[s] for s in ("Mg", "Ca")) > IE1["K"])
# ---- Q4 N vs O
ok(IE1["O"] < IE1["N"] and Z["O"] > Z["N"] and group_period(Z["O"])[0] == group_period(Z["N"])[0])
ok(config(8)["2p"] == 4 and config(7)["2p"] == 3)
C.textopt("**4.**", "A", "pair of electrons")
# ---- Q5 EA equation
o = C.options("**5.**")
ok(o["E"] == "Cl(g) + e⁻ → Cl⁻(g)")
ok(sum(1 for v in o.values() if v.startswith("Cl(g) + e")) == 1)
ok([C.key_letter(i) for i in range(1, 6)] == list("DBCAE"))
C.done()
