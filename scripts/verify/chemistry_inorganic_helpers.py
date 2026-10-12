"""Shared helpers for the chemistry verify scripts (inorganic_* and analytical_*)."""
import sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker as _Base

SUP = str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "-0123456789")

# Rounded atomic masses used in the material (g/mol)
M = {"H": 1, "He": 4, "Li": 7, "C": 12, "N": 14, "O": 16, "F": 19, "Na": 23, "Mg": 24, "Al": 27, "Si": 28,
     "P": 31, "S": 32, "Cl": 35.5, "K": 39, "Ca": 40, "Fe": 56, "Cu": 63.5, "Zn": 65, "Ag": 108, "Ba": 137, "Br": 80, "I": 127}
SYMBOLS = ("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
           "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba").split()
Z = {s: i + 1 for i, s in enumerate(SYMBOLS)}

ORDER = ["1s", "2s", "2p", "3s", "3p", "4s", "3d", "4p", "5s", "4d", "5p", "6s"]
CAP = {"s": 2, "p": 6, "d": 10}
EXCEPT = {24: {"4s": 1, "3d": 5}, 29: {"4s": 1, "3d": 10}}   # Cr, Cu


def config(z):
    """Ground-state occupation {subshell: electrons} by the Madelung order (+ Cr, Cu, Pd exceptions)."""
    occ, left = {}, z
    for sh in ORDER:
        n = min(left, CAP[sh[1]])
        if n:
            occ[sh] = n
        left -= n
        if not left:
            break
    for k, v in EXCEPT.get(z, {}).items():
        occ[k] = v
    return {k: v for k, v in occ.items() if v}


def group_period(z):
    """(period, IUPAC group 1-18) from the electron configuration."""
    occ = config(z)
    period = max(int(s[0]) for s in occ)
    s_e = occ.get(f"{period}s", 0)
    p_e = occ.get(f"{period}p", 0)
    d_e = occ.get(f"{period - 1}d", 0)
    if z == 2:
        return 1, 18
    if p_e:
        return period, 10 + s_e + p_e
    return period, s_e + d_e


def unpaired(occ):
    """Number of unpaired electrons, filling each subshell by Hund's rule."""
    n = 0
    for sh, e in occ.items():
        orbitals = {"s": 1, "p": 3, "d": 5}[sh[1]]
        n += e if e <= orbitals else 2 * orbitals - e
    return n


class Checker(_Base):
    def val(self, s):
        s = s.replace("−", "-").replace(" ", " ").replace("\xa0", " ")
        m = re.search(r"(-?\d[\d ,]*(?:\.\d+)?)\s*×\s*10([⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+)", s)
        if m:
            return float(re.sub(r"[ ,]", "", m.group(1))) * 10 ** int(m.group(2).translate(SUP))
        m = re.search(r"-?\d[\d ,]*(?:\.\d+)?|-?\.\d+", s)
        return float(re.sub(r"[ ,]", "", m.group(0))) if m else None

    def _opts5(self, label):
        o = self.options(label)
        self.ok(len(o) == 5 and len(set(o.values())) == 5, f"{label}: 5 distinct options")
        return o

    def _key(self, label, letter):
        if label.startswith("**") and label[2].isdigit():
            self.ok(self.key_letter(int(label[2])) == letter, f"{label}: key letter is not {letter}")

    def numopt(self, label, value, letter, tol=0.01):
        """Option `letter` equals value, no other option does, and (for Check questions) the key agrees."""
        o = self._opts5(label)
        hits = [k for k, v in o.items() if self.val(v) is not None and abs(self.val(v) - value) <= tol * max(abs(value), 1e-9)]
        self.ok(hits == [letter], f"{label}: options matching {value}: {hits}, expected {letter}")
        self._key(label, letter)

    def distract(self, label, letter, value, tol=0.01):
        v = self.val(self.options(label)[letter])
        self.ok(v is not None and abs(v - value) <= tol * max(abs(value), 1e-9), f"{label} ({letter}) = {v}, expected {value}")

    def textopt(self, label, letter, *phrases):
        """Option `letter` contains every phrase; key agrees (for Check questions)."""
        o = self._opts5(label)
        for p in phrases:
            self.ok(p in o[letter], f"{label}: option {letter} should contain {p!r}: {o[letter]!r}")
        self._key(label, letter)

    def only_contains(self, label, phrase, letter):
        """Exactly one option contains `phrase`, and it is `letter`."""
        o = self._opts5(label)
        hits = [k for k, v in o.items() if phrase in v]
        self.ok(hits == [letter], f"{label}: options containing {phrase!r}: {hits}, expected {letter}")
        self._key(label, letter)
