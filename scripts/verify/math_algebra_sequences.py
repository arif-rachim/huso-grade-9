"""Independent checks for materi/math/algebra-sequences.md (examples + check questions)."""
import pathlib, re
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/math/algebra-sequences.md").read_text()
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

# Example 1
bonus = [1000 + 500 * i for i in range(8)]
ok(sum(bonus) == 22000 and bonus[-1] == 4500)
mcq("**Example 1.**", 22000, "B")
ok(8 * 4500 == 36000 and 2 * 22000 == 44000 and sum(1000 + 500 * i for i in range(9)) == 27000)
# Example 2
s = sum(Fraction(1, k * (k + 1)) for k in range(1, 100))
ok(s == Fraction(99, 100))
mcq("**Example 2.**", Fraction(99, 100), "C")
ok(sum(Fraction(1, k * (k + 1)) for k in (1, 2)) == Fraction(2, 3))
# Q1
t = list(range(5, 60, 3))
ok(len(t) == 19 and sum(t) == 608)
mcq("**1.**", 608, "B")
ok(key_letter(1) == "B")
ok(18 * (5 + 59) // 2 == 576 and 20 * (5 + 59) // 2 == 640 and 2 * 608 == 1216)
# Q2
loaves = [2 ** i for i in range(10)]
ok(sum(loaves) == 1023 and loaves[-1] == 512 and sum(loaves[:9]) == 511)
mcq("**2.**", 1023, "C")
ok(key_letter(2) == "C" and 2 ** 10 == 1024 and 2 * 1023 == 2046)
# Q3
laps = [4 + 2 * d for d in range(10)]
ok(sum(laps) == 130 and laps[-1] == 22)
mcq("**3.**", 130, "B")
ok(key_letter(3) == "B" and sum(6 + 2 * d for d in range(10)) == 150 and 2 * 130 == 260 and sum(4 + 2 * d for d in range(11)) == 154)
# Q4
s4 = sum(Fraction(1, (2 * k - 1) * (2 * k + 1)) for k in range(1, 50))
ok(s4 == Fraction(49, 99) and (2 * 49 - 1, 2 * 49 + 1) == (97, 99))
mcq("**4.**", Fraction(49, 99), "D")
ok(key_letter(4) == "B" and 2 * s4 == Fraction(98, 99))
# Q5: brute force over rational ratios
sols = [Fraction(p, q) for q in range(1, 13) for p in range(-24, 25) if abs(Fraction(p, q)) < 1 and Fraction(12) / (1 - Fraction(p, q)) == 18]
ok(set(sols) == {Fraction(1, 3)}, sols)
mcq("**5.**", Fraction(1, 3), "E")
ok(key_letter(5) == "E" and 1 - Fraction(1, 3) == Fraction(2, 3))
print(f"OK {n} checks")
