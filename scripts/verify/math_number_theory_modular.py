"""Independent checks for materi/math/number-theory-modular.md (examples + check questions)."""
import pathlib, re, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/math/number-theory-modular.md").read_text()
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

def side(r):  # simulate: 12 rounds A, 12 rounds B, repeat
    seq = []
    while len(seq) < r:
        seq += ["A"] * 12 + ["B"] * 12
    return seq[r - 1]

def divisors(m): return [d for d in range(1, m + 1) if m % d == 0]
def factor(m):
    f, p = {}, 2
    while m > 1:
        while m % p == 0: f[p] = f.get(p, 0) + 1; m //= p
        p += 1
    return f

# Example 1
ok(side(100) == "A")
same = [r for r in (61, 70, 85, 96, 108) if side(r) == side(100)]
ok(same == [108], same)
mcq("**Example 1.**", 108, "E")
ok(100 % 24 == 4 and 96 % 24 == 0 and 61 % 24 == 13 and 70 % 24 == 22 and 85 % 24 == 13)
# Example 2
ds = divisors(360)
ok(len(ds) == 24 and factor(360) == {2: 3, 3: 2, 5: 1} and 4 * 3 * 2 == 24)
boxes = [d for d in ds if d > 1 and 360 // d > 1]
ok(len(boxes) == 22 and 3 + 2 + 1 == 6)
mcq("**Example 2.**", 22, "B")
# core-idea facts
ok(17 * 23 % 5 == 2 * 3 % 5 and [pow(2, k, 7) for k in range(1, 7)] == [2, 4, 1, 2, 4, 1])
ok([pow(7, k, 10) for k in range(1, 6)] == [7, 9, 3, 1, 7] and 100 % 24 == 4 and (17 - (-3)) % 20 == 0)
ok(2 * 3 % 6 == 2 * 6 % 6 and 3 % 6 != 6 % 6)
# Q1
r = 1
for _ in range(100): r = r * 2 % 7
ok(r == 2 and pow(2, 2, 7) == 4)
mcq("**1.**", 2, "B"); ok(key_letter(1) == "B")
# Q2
scouts = [(i % 5) + 1 for i in range(2030)]
ok(scouts[0] == 1 and scouts[5] == 1 and scouts[-1] == 5 and 2030 % 5 == 0)
o = options("**2.**"); ok(key_letter(2) == "E" and o["E"] == "Player 5" and len(set(o.values())) == 5)
# Q3
cand = [k for k in range(1, 100) if k % 3 == 2 and k % 5 == 3]
ok(cand[0] == 8 and cand[1:3] == [23, 38] and 13 % 3 == 1 and 5 % 5 == 0 and 11 % 5 == 1)
mcq("**3.**", 8, "C"); ok(key_letter(3) == "C")
ok(13 % 3 == 1 and 23 % 3 == 2 and 23 % 5 == 3)
# Q4
f = factor(1001)
ok(f == {7: 1, 11: 1, 13: 1} and sum(f) == 31)
mcq("**4.**", 31, "D"); ok(key_letter(4) == "D" and 11 + 13 == 24)
# Q5
ks = [k for k in range(1, 50) if math.isqrt(72 * k) ** 2 == 72 * k]
ok(ks[0] == 2 and 8 in ks and 3 not in ks and 6 not in ks and 12 not in ks)
mcq("**5.**", 2, "A"); ok(key_letter(5) == "A")
print(f"OK {n} checks")
