"""Shared helpers for the geosphere_* and astronomy_* Earth Science verify scripts.

Checker parses a materi file (options, answer key) and offers:
  * numbers: mcq()/opt_is() recompute a numeric answer and match it to exactly one option
  * facts:   fact_checks() takes a list of (text that must appear in the file, truth, source)
             where `truth` is a bool computed from a small reference table or a calculation
  * choices: choice() checks a conceptual question: the key letter, the option text, and that
             every other option is wrong according to a predicate over the option text
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]


class Checker:
    def __init__(self, md):
        self.txt = (ROOT / md).read_text()
        self.n = 0

    def ok(self, cond, msg="check failed"):
        assert cond, msg
        self.n += 1

    # ---- parsing -------------------------------------------------------------------------
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

    # ---- numbers -------------------------------------------------------------------------
    @staticmethod
    def first_number(s):
        s = s.replace("−", "-").replace(",", "")
        s = re.sub(r"\s*×\s*10", "e", s)
        sup = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
        s = s.translate(sup)
        m = re.search(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", s)
        return None if not m else float(m.group(0))

    def numeric_options(self, label):
        o = self.options(label)
        return {k: Checker.first_number(v) for k, v in o.items()}

    def mcq(self, label, value, letter, tol=0.011):
        """Exactly one option's leading number equals `value` (relative tol) and it is `letter`; key agrees."""
        o = self.numeric_options(label)
        self.ok(len(self.options(label)) == 5 and len(set(self.options(label).values())) == 5, f"{label}: 5 distinct options")
        hits = [k for k, v in o.items() if v is not None and abs(v - value) <= max(tol * abs(value), 1e-9)]
        self.ok(hits == [letter], f"{label}: {hits} vs {letter} (value {value}) {o}")
        if label.startswith("**") and label[2].isdigit():
            self.ok(self.key_letter(int(label[2])) == letter, f"{label}: key letter")

    def opt_is(self, label, letter, value, tol=0.011):
        """A distractor note: option `letter` equals the wrong-path value."""
        v = self.numeric_options(label)[letter]
        self.ok(v is not None and abs(v - value) <= max(tol * abs(value), 1e-9), f"{label} option {letter}: {v} vs {value}")

    # ---- concepts ------------------------------------------------------------------------
    def choice(self, label, letter, right, wrong=None):
        """right(text)->True only for the correct option; the key letter must be `letter`.
        `right` encodes the science fact; all other options must fail it."""
        o = self.options(label)
        self.ok(len(o) == 5 and len(set(o.values())) == 5, f"{label}: 5 distinct options")
        hits = [k for k, v in o.items() if right(v)]
        self.ok(hits == [letter], f"{label}: options satisfying the fact: {hits}, expected [{letter}]")
        if label.startswith("**") and label[2].isdigit():
            self.ok(self.key_letter(int(label[2])) == letter, f"{label}: key letter")

    def key_mentions(self, q, *phrases):
        k = self.key_text(q)
        for p in phrases:
            self.ok(p in k, f"key {q} should mention {p!r}")

    # ---- facts ---------------------------------------------------------------------------
    def fact_checks(self, facts):
        """facts: list of (fragment, truth(bool), source). The fragment must appear in the file."""
        for frag, truth, src in facts:
            self.ok(frag in self.txt, f"fact text missing from the file: {frag!r}")
            self.ok(bool(truth), f"fact is not true by the reference ({src}): {frag!r}")

    def finish(self, keys):
        got = [self.key_letter(q) for q in range(1, 6)]
        self.ok(got == list(keys), f"keys {got} vs {list(keys)}")
        self.ok(max(got.count(c) for c in "ABCDE") <= 2, "a letter is used more than twice")
        print(f"OK {self.n} checks")
