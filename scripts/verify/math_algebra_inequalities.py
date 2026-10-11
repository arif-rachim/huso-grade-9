"""Independent checks for materi/math/algebra-inequalities.md (examples + check questions)."""
import pathlib, re, itertools, math
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/math/algebra-inequalities.md").read_text()
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

# Hook: perimeter 24 rectangles
areas = {w: w * (12 - w) for w in range(1, 12)}
ok(max(areas.values()) == 36 and areas[6] == 36 and areas[1] == 11 and areas[9] == 27 and areas[8] == 32)
# Example 1: 2x + y = 120, brute force over x in half steps
best = max((Fraction(x2, 2) * (120 - 2 * Fraction(x2, 2)), Fraction(x2, 2)) for x2 in range(1, 120))
ok(best == (1800, 30), best)
mcq("**Example 1.**", 1800, "C")
ok(30 * 30 == 900 and 40 * 40 == 1600 and 60 * 60 == 3600)
# Example 2: sides 7, 12
good = [x for x in range(1, 40) if x + 7 > 12 and x + 12 > 7 and 7 + 12 > x]
ok(len(good) == 13 and good[0] == 6 and good[-1] == 18)
mcq("**Example 2.**", 13, "C")
ok(len([x for x in range(5, 20)]) == 15)
# Q1
vals = [Fraction(i, 100) ** 2 - 6 * Fraction(i, 100) + 11 for i in range(-1000, 1001)]
ok(min(vals) == 2 and Fraction(3) ** 2 - 18 + 11 == 2)
mcq("**1.**", 2, "C"); ok(key_letter(1) == "C")
ok(3 ** 2 - 18 + 11 == 2 and 9 - 9 + 0 == 0)
# Q2
grid = [Fraction(i, 1000) for i in range(1, 20001)]
f = lambda x: 4 * x + 9 / x
ok(min(f(x) for x in grid) == 12 and f(Fraction(3, 2)) == 12 and f(1) == 13)
mcq("**2.**", 12, "B"); ok(key_letter(2) == "B")
# Q3
t = Fraction(50) / 1 + Fraction(50) / Fraction(3, 2)
ok(Fraction(100) / t == Fraction(6, 5) and Fraction(6, 5) == 2 / (1 + Fraction(2, 3)))
mcq("**3.**", Fraction(6, 5), "C"); ok(key_letter(3) == "C")
ok(Fraction(5, 4) == (1 + Fraction(3, 2)) / 2)
# Q4
tri = [(a, b, c) for a, b, c in itertools.product([4], [9], range(1, 40)) if a + b > c and a + c > b and b + c > a]
per = [sum(t_) for t_ in tri]
ok(min(per) == 19 and max(per) == 25 and 4 + 9 + 5 == 18)
mcq("**4.**", 19, "B"); ok(key_letter(4) == "B")
# Q5
pts = [Fraction(i, 2) for i in range(-8, 9)]
def sqrt_ok(v): return v >= 0
stmts = {
    "A": lambda a, b: a * a + b * b >= 2 * a * b,
    "B": lambda a, b: (a + b) ** 2 >= 4 * a * b,
    "C": lambda a, b: a * a + 1 >= 2 * a,
    "D": lambda a, b: (a + b) / 2 >= math.sqrt(a * b) if a * b >= 0 else True,
    "E": lambda a, b: a * a + b * b >= -2 * a * b,
}
fails = [k for k, fn in stmts.items() if not all(fn(a, b) for a in pts for b in pts)]
ok(fails == ["D"], fails)
o = options("**5.**"); ok(len(o) == 5 and key_letter(5) == "D")
ok(stmts["D"](-1, -1) is False or not stmts["D"](-1, -1))
print(f"OK {n} checks")
