"""Shared helpers for the chemistry verify scripts of part 2 (parse numbers like '6.3 × 10⁻⁵ M' from the markdown options)."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker  # noqa: E402

SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def parse(s):
    """First number in a string -> (value, half-unit of its last printed digit). Handles '−', thousands spaces, '× 10⁻⁵'."""
    s = s.replace("−", "-").replace(" ", " ").replace(" ", " ")
    m = re.match(r"\s*([+-]?\d[\d ,]*(?:\.\d+)?|[+-]?\.\d+)\s*(?:×\s*10([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+))?", s)
    if not m:
        return None, None
    txt = re.sub(r"[ ,]", "", m.group(1))
    v = float(txt)
    dec = len(txt.split(".")[1]) if "." in txt else 0
    half = 0.5 * 10 ** (-dec)
    if m.group(2):
        e = int(m.group(2).translate(SUP))
        v *= 10 ** e
        half *= 10 ** e
    return v, half


class Chk(Checker):
    def mcq2(self, label, value, letter, tol=0.0, unit_filter=None):
        """Exactly one option parses to `value` (within its own rounding or relative tol) and it is `letter`; key agrees."""
        o = self.options(label)
        self.ok(len(o) == 5 and len(set(o.values())) == 5, f"{label}: 5 distinct options")
        hits = []
        for k, t in o.items():
            if unit_filter and unit_filter not in t:
                continue
            v, half = parse(t)
            if v is None:
                continue
            if abs(v - value) <= max(tol * abs(value), half * 1.0001):
                hits.append(k)
        self.ok(hits == [letter], f"{label}: matches {hits}, wanted {letter} (value {value})")
        if label.startswith("**") and label[2].isdigit():
            self.ok(self.key_letter(int(label[2])) == letter, f"{label}: key letter")

    def opt2(self, label, letter, value, tol=0.0):
        v, half = parse(self.options(label)[letter])
        self.ok(v is not None and abs(v - value) <= max(tol * abs(value), half * 1.0001),
                f"{label} option {letter} = {self.options(label)[letter]!r}, expected {value}")

    def text_key(self, label, letter, phrase):
        """Concept question: key is `letter`, and `phrase` is in that option but in no other option."""
        o = self.options(label)
        self.ok(phrase.lower() in o[letter].lower(), f"{label}: {phrase!r} not in option {letter}")
        for k, t in o.items():
            if k != letter:
                self.ok(phrase.lower() not in t.lower(), f"{label}: {phrase!r} also in option {k}")
        if label.startswith("**") and label[2].isdigit():
            self.ok(self.key_letter(int(label[2])) == letter, f"{label}: key letter")

    def letters_spread(self):
        """No letter is the key more than twice."""
        ks = [self.key_letter(q) for q in range(1, 6)]
        self.ok(all(ks.count(k) <= 2 for k in set(ks)), f"letter spread {ks}")
