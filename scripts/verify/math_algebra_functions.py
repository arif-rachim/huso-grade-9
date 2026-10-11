"""Independent checks for materi/math/algebra-functions.md (examples + check questions)."""
import pathlib, re, math
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/math/algebra-functions.md").read_text()
n = 0

def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1

def num(s):
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s).replace("−", "-").strip()
    return Fraction(re.match(r"-?\d+(?:\.\d+)?(?:/\d+)?", s).group(0))

def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    return dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))

def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", TXT.split("<details>")[1], re.M).group(1)

def mcq(label, value, key, conv=num):
    o = options(label)
    ok(len(set(o.values())) == 5, "options distinct")
    hits = [k for k, v in o.items() if conv(v) == value]
    ok(hits == [key], f"{label}: {hits} vs {key}")

# Hook: 130 m in 50 m pool
ok(130 // 50 == 2 and -(-130 // 50) == 3)
# floor/ceiling facts from the text
ok((math.floor(2.3), math.ceil(2.3), math.floor(-2.3), math.ceil(-2.3)) == (2, 3, -3, -2))
# trig table
for deg, s, c in [(30, 0.5, math.sqrt(3) / 2), (45, math.sqrt(2) / 2, math.sqrt(2) / 2), (60, math.sqrt(3) / 2, 0.5)]:
    r = math.radians(deg)
    ok(abs(math.sin(r) - s) < 1e-12 and abs(math.cos(r) - c) < 1e-12 and abs(math.sin(r) ** 2 + math.cos(r) ** 2 - 1) < 1e-12)
ok(abs(math.tan(math.radians(30)) - math.sqrt(3) / 3) < 1e-12 and abs(math.tan(math.radians(60)) - math.sqrt(3)) < 1e-12)
ok(abs(math.log2(8) - 3) < 1e-12)

# Example 1: smallest whole number of 25 m lengths covering >= 410 m
L = next(k for k in range(1, 100) if 25 * k >= 410)
ok(L == 17 and 25 * L == 425 and 16 * 25 == 400 and 18 * 25 == 450)
mcq("**Example 1.**", 425, "C")
# Example 2: brute-force rational f(0), f(1)
cands = [Fraction(p, q) for q in range(1, 7) for p in range(-12, 13)]
sol = {(a, b) for a in cands for b in cands if a + 2 * b == 0 and b + 2 * a == 1}
ok(sol == {(Fraction(2, 3), Fraction(-1, 3))}, sol)
f = lambda x: (x * x - 4 * x + 2) / 3
ok(all(f(Fraction(k, 3)) + 2 * f(1 - Fraction(k, 3)) == Fraction(k, 3) ** 2 for k in range(-30, 31)))
mcq("**Example 2.**", Fraction(2, 3), "D")

# Q1: test candidates on a window of the integers
W = range(-60, 61)
cand = {"A": lambda x: 2 * x, "B": lambda x: x * x, "C": lambda x: x ** 3, "D": abs, "E": lambda x: x + 3}
def inj(fn): return len({fn(x) for x in W}) == len(W)
def surj(fn): return all(any(fn(x) == y for x in W) for y in range(-5, 6))
good = [k for k, fn in cand.items() if inj(fn) and surj(fn)]
ok(good == ["E"], good)
ok(not surj(cand["C"]) and inj(cand["C"]))
o = options("**1.**"); ok(len(set(o.values())) == 5 and key_letter(1) == "E")
# Q2
fo = lambda x: Fraction(5, 2) * x
ge = lambda x: Fraction(3, 4) * x * x
ok(fo(2) == 5 and ge(2) == 3 and fo(-2) + ge(-2) == -2 and -5 - 3 == -8 and 5 + 3 == 8)
mcq("**2.**", -2, "B"); ok(key_letter(2) == "B")
# Q3
c = next(k for k in range(1, 100) if 6 * k >= 100); e = 6 * c - 100
ok((c, e) == (17, 2) and c + e == 19 and 16 + 4 == 20)
mcq("**3.**", 19, "D"); ok(key_letter(3) == "D")
# Q4
val = math.log2(math.cos(math.radians(60))) + math.log(27, 3)
ok(abs(val - 2) < 1e-9)
o = options("**4.**"); ok(key_letter(4) == "A" and num(o["A"]) == 2 and len(set(o.values())) == 5)
ok(abs(-math.log2(math.cos(math.radians(60))) + 3 - 4) < 1e-9)
# Q5
vals = [3]
for _ in range(5): vals.append(2 * vals[-1])
ok(vals[4] == 48 and vals[2] == 12 and vals[3] == 24 and vals[5] == 96)
ok(all(3 * 2 ** (x + 1) == 2 * (3 * 2 ** x) for x in range(-5, 6)))
mcq("**5.**", 48, "D"); ok(key_letter(5) == "D")
print(f"OK {n} checks")
