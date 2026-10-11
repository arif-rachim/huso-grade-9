"""Independent checks for materi/math/number-theory-misc.md (examples + check questions)."""
import pathlib, re, math, itertools

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/math/number-theory-misc.md").read_text()
n = 0

def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1

def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    return dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))

def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", TXT.split("<details>")[1], re.M).group(1)

def mcq(label, value, key, conv=lambda s: int(re.search(r"\d+", s).group(0))):
    o = options(label)
    ok(len(set(o.values())) == 5, "options distinct")
    hits = [k for k, v in o.items() if conv(v) == value]
    ok(hits == [key], f"{label}: {hits} vs {key}")

def to_base(m, b):
    d = []
    while m: d.append(m % b); m //= b
    return "".join(map(str, reversed(d))) or "0"

# Hook: packs of 3 and 5
mk = lambda t, a, b: any(t == a * x + b * y for x in range(t + 1) for y in range(t + 1))
ok(mk(14, 3, 5) and not mk(7, 3, 5) and 3 * 5 - 3 - 5 == 7)
# Example 1: packs 4 and 7
can = [t for t in range(1, 200) if mk(t, 4, 7)]
cant = [t for t in range(1, 200) if not mk(t, 4, 7)]
ok(max(cant) == 17 and cant == [1, 2, 3, 5, 6, 9, 10, 13, 17] and all(t in can for t in range(18, 200)))
ok(all(t in can for t in (18, 19, 20, 21)) and 4 * 7 - 4 - 7 == 17 and 18 == 4 + 7 + 7)
mcq("**Example 1.**", 17, "C")
# Example 2: base b numeral 132 == 42
bs = [b for b in range(4, 60) if 1 * b * b + 3 * b + 2 == 42]
ok(bs == [5] and 6 * 6 + 18 + 2 == 56)
mcq("**Example 2.**", 5, "B")
# core facts
ok(math.gcd(6, 9) == 3 and not any(6 * x + 9 * y == 50 for x in range(-60, 61) for y in range(-60, 61)))
ok(int("1011", 2) == 11 and to_base(45, 3) == "1200" and int("1200", 3) == 45)
for a, b, c in [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29), (9, 40, 41), (6, 8, 10), (9, 12, 15)]:
    ok(a * a + b * b == c * c)
ok(6 ** 2 + 8 ** 2 != 11 ** 2 and 15 ** 2 + 20 ** 2 == 625 and 625 != 26 ** 2)
for m_, n_ in [(2, 1), (3, 2), (4, 1), (4, 3), (5, 2)]:
    ok((m_ * m_ - n_ * n_) ** 2 + (2 * m_ * n_) ** 2 == (m_ * m_ + n_ * n_) ** 2)
ok(all(len([s for r in range(6) for s in itertools.combinations([1, 2, 4, 8, 16], r) if sum(s) == t]) == 1 for t in range(1, 32)))
# Q1
sol = [(x, y) for x in range(1, 50) for y in range(1, 50) if 3 * x + 5 * y == 41]
ok(sol == [(2, 7), (7, 4), (12, 1)])
mcq("**1.**", 3, "C"); ok(key_letter(1) == "C")
# Q2
cands = [(w, d) for w in range(1, 100) for d in [26] if 24 ** 2 + w ** 2 == d ** 2]
ok(cands == [(10, 26)] and 2 * (24 + 10) == 68)
mcq("**2.**", 68, "D"); ok(key_letter(2) == "D")
ok(24 + 26 == 50 and 2 * 26 == 52 and 34 * 2 == 68 and 68 * 2 == 136)
# Q3
ok(to_base(50, 4) == "302")
o = options("**3.**"); ok(len(set(o.values())) == 5 and o["B"] == "302" and key_letter(3) == "B")
ok(int("320", 4) == 56 and int("322", 4) == 58 and int("203", 4) == 35)
# Q4
subs = [s for r in range(6) for s in itertools.combinations([1, 2, 4, 8, 16], r) if sum(s) == 27]
ok(subs == [(1, 2, 8, 16)] and 16 + 8 + 4 == 28)
mcq("**4.**", 4, "C"); ok(key_letter(4) == "C")
# Q5
nosol = [c for c in (50, 12, 21, 30, 45) if not any(6 * x + 9 * y == c for x in range(-60, 61) for y in range(-60, 61))]
ok(nosol == [50])
mcq("**5.**", 50, "A"); ok(key_letter(5) == "A")
print(f"OK {n} checks")
