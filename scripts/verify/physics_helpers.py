"""Small shared helpers for the physics verify scripts (parse the markdown options and key)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SI = {"": 1.0, "k": 1e3, "M": 1e6, "m": 1e-3}


class Checker:
    def __init__(self, md):
        self.txt = (ROOT / md).read_text()
        self.n = 0

    def ok(self, cond, msg="check failed"):
        assert cond, msg
        self.n += 1

    def options(self, label):
        i = self.txt.index(label)
        line = next(l for l in self.txt[i:].splitlines() if l.startswith("(A)"))
        return dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))

    def key_letter(self, q):
        key = self.txt.split("<details>")[1]
        return re.search(rf"^{q}\. \*\*\(([A-E])\)", key, re.M).group(1)

    def key_text(self, q):
        key = self.txt.split("<details>")[1]
        return re.search(rf"^{q}\. (.*)$", key, re.M).group(1)

    @staticmethod
    def num(s, unit):
        """Parse '1 336 kJ' / '0.021 MJ' / '44 °C' into a number in the base `unit` (J, °C, m, ...)."""
        s = s.replace("−", "-").replace(" ", " ").strip()
        m = re.match(r"([+-]?[\d ,]*\d(?:\.\d+)?)\s*([kMm]?)" + re.escape(unit) + r"$", s)
        if not m:
            return None
        v = float(re.sub(r"[ ,]", "", m.group(1)))
        dec = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
        Checker.last_half = 0.5 * 10 ** (-dec) * SI[m.group(2)]   # rounding slack of the printed number
        return v * SI[m.group(2)]

    def mcq(self, label, value, unit, letter, tol=0.005):
        """Exactly one option equals `value` (relative tol) and it is `letter`; the key agrees."""
        o = self.options(label)
        self.ok(len(o) == 5 and len(set(o.values())) == 5, f"{label}: 5 distinct options")
        hits = []
        for k, v in o.items():
            x = self.num(v, unit)
            if x is not None and abs(x - value) <= max(tol * max(abs(value), 1e-12), Checker.last_half * 1.0001):
                hits.append(k)
        self.ok(hits == [letter], f"{label}: {hits} vs {letter} (value {value})")
        if label.startswith("**") and label[2].isdigit():
            self.ok(self.key_letter(int(label[2])) == letter, f"{label}: key letter")

    def opt_is(self, label, letter, value, unit, tol=0.005):
        """Assert option `letter` of the question equals `value` (used for distractor claims)."""
        x = self.num(self.options(label)[letter], unit)
        self.ok(x is not None and abs(x - value) <= max(tol * max(abs(value), 1e-12), Checker.last_half * 1.0001),
                f"{label} option {letter} = {self.options(label)[letter]!r}, expected {value}")

    def key_mentions(self, q, *phrases):
        k = self.key_text(q)
        for p in phrases:
            self.ok(p in k, f"key {q} should mention {p!r}")

    def done(self):
        print(f"OK {self.n} checks")
