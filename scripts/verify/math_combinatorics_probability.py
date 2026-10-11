"""Independent brute-force checks for materi/math/combinatorics-probability.md."""
import itertools
from fractions import Fraction as F

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1

# Example 1: tree. Model as a weighted enumeration of the 4 stories
p1 = F(6, 10)
p2_given = {True: F(7, 10), False: F(5, 10)}
stories = []
for w1, w2 in itertools.product([True, False], repeat=2):
    pr = (p1 if w1 else 1 - p1) * (p2_given[w1] if w2 else 1 - p2_given[w1])
    stories.append((w1, w2, pr))
ok(sum(s[2] for s in stories) == 1, "probabilities sum to 1")
pw2 = sum(s[2] for s in stories if s[1])
ok(pw2 == F(62, 100), pw2)
ok(F(42, 100) / pw2 == F(21, 31), "bonus 21/31")
ok(p1 * p2_given[True] == F(42, 100) and (1 - p1) * p2_given[False] == F(2, 10), "ex1 paths")
# Monte-Carlo-free exact check with integer counting: 100-round universe
ok(60 * 70 // 100 + 40 * 50 // 100 == 62, "ex1 counting universe of 100")

# Example 2: cookies
cookies = ["C"] * 5 + ["P"] * 3
pairs = list(itertools.combinations(range(8), 2))
atleast = [p for p in pairs if any(cookies[i] == "C" for i in p)]
both = [p for p in pairs if all(cookies[i] == "C" for i in p)]
ok(len(pairs) == 28 and len(atleast) == 25 and len(both) == 10, "ex2 counts")
ok(F(len(both), len(atleast)) == F(2, 5), "ex2")
ok(F(10, 28) == F(5, 14) and F(25, 28) == F(len(atleast), 28), "ex2 distractors")

# Q1
ok(F(sum(1 for a, b in itertools.product(range(1, 7), repeat=2) if a + b == 8), 36) == F(5, 36), "q1")
ok(F(sum(1 for a, b in itertools.product(range(1, 7), repeat=2) if a + b == 7), 36) == F(1, 6), "q1 distractor")
# Q2
pm = F(2, 5)
p_none = sum((pm if s else 1 - pm) * (pm if t else 1 - pm) * (pm if u else 1 - pm)
             for s, t, u in itertools.product([0, 1], repeat=3) if not (s or t or u))
ok(1 - p_none == F(784, 1000) and p_none == F(216, 1000) and pm**3 == F(64, 1000), "q2")
ok(1 - pm**3 == F(936, 1000), "q2 distractor")
# Q3
c3 = [k for k in range(1, 21) if k % 3 == 0 or k % 4 == 0]
ok(F(len(c3), 20) == F(1, 2), "q3")
ok(F(6 + 5, 20) == F(11, 20), "q3 distractor")
# Q4: 50 swimmers; 30 free, 25 back, 10 both (5 neither)
swim = [(1, 1)] * 10 + [(1, 0)] * 20 + [(0, 1)] * 15 + [(0, 0)] * 5
ok(len(swim) == 50 and sum(s[0] for s in swim) == 30 and sum(s[1] for s in swim) == 25, "q4 data")
free = [s for s in swim if s[0]]
ok(F(sum(s[1] for s in free), len(free)) == F(1, 3), "q4")
ok(F(10, 50) == F(1, 5) and F(10, 25) == F(2, 5), "q4 distractors")
# Q5
jar = ["R"] * 3 + ["G"] * 2
same = sum(1 for a, b in itertools.permutations(range(5), 2) if jar[a] == jar[b])
ok(F(same, 20) == F(2, 5), "q5")
withrep = sum(1 for a, b in itertools.product(range(5), repeat=2) if jar[a] == jar[b])
ok(F(withrep, 25) == F(13, 25), "q5 distractor")
print(f"OK {n} checks")
