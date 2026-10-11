"""Independent brute-force checks for materi/math/combinatorics-strategies.md."""
import itertools, math
from fractions import Fraction as F

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1

# Example 1: lanes, A and B not neighbours
good = sum(1 for p in itertools.permutations(range(6)) if abs(p.index(0) - p.index(1)) != 1)
bad = sum(1 for p in itertools.permutations(range(6)) if abs(p.index(0) - p.index(1)) == 1)
ok(good == 480 and bad == 240, (good, bad))
ok(720 - 5 * 24 == 600 and 720 // 2 == 360 and 720 - 120 == 600, "ex1 distractors")
ok(F(5, math.comb(6, 2)) == F(1, 3), "ex1 symmetry")

# Example 2: grid paths 4 right, 3 up
def paths(w, h):
    return 1 if w == 0 or h == 0 else paths(w - 1, h) + paths(w, h - 1)
ok(paths(4, 3) == 35, "ex2 recursion")
ok(sum(1 for s in itertools.product("RU", repeat=7) if s.count("R") == 4) == 35, "ex2 strings")
ok(math.comb(8, 4) == 70 and 2**7 == 128 and 4 * 3 == 12 and math.comb(7, 2) == 21, "ex2 distractors")

# Q1: 4-digit numbers containing a 7
c1 = sum(1 for k in range(1000, 10000) if "7" in str(k))
ok(c1 == 3168, c1)
ok(sum(1 for k in range(1000, 10000) if "7" not in str(k)) == 5832, "q1 no-7")
ok(9000 - 9**4 == 2439 and 4 * 1000 == 4000, "q1 distractors")
# Q2: coin change 20 cents
c2 = sum(1 for t in range(3) for f in range(5) if 10 * t + 5 * f <= 20)
ok(c2 == 9, c2)
ok(sum(1 for t in range(3) for f in range(5) for p in range(21) if 10 * t + 5 * f + p == 20) == 9, "q2 explicit")
# casework example for 10 cents
ok(sum(1 for t in range(2) for f in range(3) if 10 * t + 5 * f <= 10) == 4, "10 cents")
# Q3: binary strings length 8, three 1s, none adjacent
c3 = [s for s in itertools.product((0, 1), repeat=8) if sum(s) == 3 and all(not (s[i] and s[i + 1]) for i in range(7))]
ok(len(c3) == 20, len(c3))
ok(math.comb(8, 3) == 56 and math.comb(6, 3) == 20, "q3 bijection / distractor")
# Q4: A in lower lane than B and C among 8 swimmers
tot = good4 = 0
for p in itertools.permutations(range(8)):
    tot += 1
    if p.index(0) < p.index(1) and p.index(0) < p.index(2): good4 += 1
ok(F(good4, tot) == F(1, 3), (good4, tot))
# Q5: even 4-digit codes from digits 1..7 no repeats
c5 = sum(1 for p in itertools.permutations(range(1, 8), 4) if p[-1] % 2 == 0)
ok(c5 == 360, c5)
ok(len(list(itertools.permutations(range(1, 8), 4))) == 840, "q5 distractor")
# subsets <-> strings
ok(sum(1 for _ in itertools.chain.from_iterable(itertools.combinations(range(5), k) for k in range(6))) == 2**5, "subsets")
# 3-digit even numbers, digits 1-9 distinct (concept example)
ok(sum(1 for p in itertools.permutations(range(1, 10), 3) if p[-1] % 2 == 0) == 4 * 8 * 7, "constructive example")
print(f"OK {n} checks")
