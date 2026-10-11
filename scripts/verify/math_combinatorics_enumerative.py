"""Independent brute-force checks for materi/math/combinatorics-enumerative.md."""
import itertools, math
from collections import Counter

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1

# Example 1: (team of 5 from 8, leader among the five)
cnt = sum(1 for team in itertools.combinations(range(8), 5) for leader in team)
ok(cnt == 280, cnt)
ok(8 * len(list(itertools.combinations(range(7), 4))) == 280, "ex1 other method")
ok(len(list(itertools.combinations(range(8), 5))) == 56 and len(list(itertools.permutations(range(8), 5))) == 6720, "ex1 distractors")
ok(len(list(itertools.permutations(range(8), 3))) == 336 and len(list(itertools.permutations(range(8), 4))) == 1680, "ex1 336/1680 exist")

# Example 2: 10 identical tomatoes into 3 different bowls, each >= 1
c2 = sum(1 for a in range(1, 11) for b in range(1, 11) if 10 - a - b >= 1)
ok(c2 == 36, c2)
c2b = sum(1 for a in range(0, 11) for b in range(0, 11) if 10 - a - b >= 0)
ok(c2b == 66, c2b)
ok(math.comb(10, 2) == 45 and math.comb(10, 3) == 120 and 10 * 3 == 30, "ex2 distractors")

# Q1: relay line-ups
ok(len(list(itertools.permutations(range(6), 4))) == 360, "q1")
ok(len(list(itertools.combinations(range(6), 4))) == 15 and math.factorial(6) == 720 and 6**4 == 1296, "q1 distractors")
# Q2: PANCAKE
ok(len(set(itertools.permutations("PANCAKE"))) == 2520, "q2")
ok(math.factorial(7) == 5040 and math.factorial(7)//2//2 == 1260, "q2 distractors")
# Q3
ok(math.comb(10, 3) + math.comb(10, 4) == 330 and math.comb(11, 4) == 330, "q3")
ok(math.comb(10, 3) == 120 and math.comb(10, 4) == 210 and math.comb(10, 5) == 252, "q3 parts")
# pascal row sums and recurrence
for r in range(0, 9):
    ok(sum(math.comb(r, k) for k in range(r+1)) == 2**r, "row sum")
ok(all(math.comb(r, k) == math.comb(r-1, k-1) + math.comb(r-1, k) for r in range(2, 8) for k in range(1, r)), "pascal rule")
# Q4
q4 = sum(1 for t in itertools.product(range(8), repeat=4) if sum(t) == 7)
ok(q4 == 120, q4)
q4p = sum(1 for t in itertools.product(range(1, 8), repeat=4) if sum(t) == 7)
ok(q4p == 20 and math.comb(10, 4) == 210, "q4 distractors")
# Q5: unlabelled split of 6 into 3+3
splits = {frozenset([frozenset(a), frozenset(set(range(6)) - set(a))]) for a in itertools.combinations(range(6), 3)}
ok(len(splits) == 10, len(splits))
ok(math.comb(6, 3) == 20, "q5 labelled")

# BOOK example and partitions of 5
ok(len(set(itertools.permutations("BOOK"))) == 12, "book")
def parts(m, mx=None):
    mx = mx or m
    if m == 0: yield (); return
    for k in range(min(m, mx), 0, -1):
        for r in parts(m - k, k): yield (k,) + r
ok(len(list(parts(5))) == 7, "p(5)")
# stars and bars picture: 5 identical into 3 bowls = 21
ok(sum(1 for t in itertools.product(range(6), repeat=3) if sum(t) == 5) == 21, "sb picture")
print(f"OK {n} checks")
