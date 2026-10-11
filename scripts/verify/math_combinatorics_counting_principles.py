"""Independent brute-force checks for materi/math/combinatorics-counting-principles.md."""
import itertools, math
from functools import lru_cache

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1

# Example 1: inclusion-exclusion, build an explicit club with the stated overlaps
# regions (G,S,R) membership counts
reg = {(1,0,0):9,(0,1,0):6,(0,0,1):5,(1,1,0):6,(1,0,1):4,(0,1,1):3,(1,1,1):3}
members = [k for k, v in reg.items() for _ in range(v)]
G = sum(m[0] for m in members); S = sum(m[1] for m in members); R = sum(m[2] for m in members)
ok((G, S, R) == (22, 18, 15), (G, S, R))
ok(sum(m[0] and m[1] for m in members) == 9 and sum(m[0] and m[2] for m in members) == 7
   and sum(m[1] and m[2] for m in members) == 6 and sum(all(m) for m in members) == 3, "overlaps")
ok(len(members) == 36 and 40 - len(members) == 4, "ex1 none")
ok(22+18+15-9-7-6+3 == 36 and 22+18+15-9-7-6 == 33 and 40-33 == 7, "ex1 distractor 7")
ok(40 - (9+6+5) == 20, "ex1 distractor 20")

# Example 2: spoons, 4 colours, guarantee 3 alike
worst = max(sum(c) for c in itertools.product(range(3), repeat=4))  # no colour reaches 3
ok(worst == 8, worst)
def guaranteed(m):
    # every distribution of m spoons over 4 colours has a colour with >= 3?
    return all(max(c) >= 3 for c in itertools.product(range(m+1), repeat=4) if sum(c) == m)
ok(not guaranteed(8) and guaranteed(9), "ex2 answer 9")

# Q1: orders
ok(len(list(itertools.product(range(4), range(3), [None, 0, 1]))) == 36, "q1")
ok(4*3*2 == 24 and 4*3 == 12 and 4+3+3 == 10 and 4+3+2 == 9, "q1 distractors")
# Q2: multiples of 4 or 6
ok(sum(1 for k in range(1, 61) if k % 4 == 0 or k % 6 == 0) == 20, "q2")
ok(15 + 10 == 25, "q2 distractor")
# Q3: largest k guaranteed among 50 students in 12 months
def best_k(N, boxes):
    # smallest possible max-load over all distributions = what is guaranteed
    # a distribution with max load m exists iff boxes*m >= N
    m = 1
    while boxes * m < N: m += 1
    return m
ok(best_k(50, 12) == 5, "q3")
# brute-force check with a smaller analogue to validate the helper
ok(best_k(7, 3) == min(max(c) for c in itertools.product(range(8), repeat=3) if sum(c) == 7), "q3 helper")
ok(12*4 == 48 < 50 and 12*5 >= 50, "q3 numbers")
# Q4: reachable final numbers
@lru_cache(None)
def reach(state):
    if len(state) == 1: return frozenset(state)
    out = set()
    for i, j in itertools.combinations(range(len(state)), 2):
        rest = [state[k] for k in range(len(state)) if k not in (i, j)]
        rest.append(abs(state[i]-state[j]))
        out |= reach(tuple(sorted(rest)))
    return frozenset(out)
final = reach(tuple(range(1, 11)))
ok(5 in final, "5 reachable")
ok(all(v % 2 == 1 for v in final), final)
ok(not ({0, 2, 4, 8} & final), "even values impossible")
# Q5: maximum domino packing on 6x6 minus opposite corners (bipartite matching)
cells = [(i, j) for i in range(6) for j in range(6) if (i, j) not in [(0, 0), (5, 5)]]
dark = [c for c in cells if (c[0]+c[1]) % 2 == 0]
light = [c for c in cells if (c[0]+c[1]) % 2 == 1]
ok((len(dark), len(light)) == (16, 18), (len(dark), len(light)))
match = {}
def aug(u, seen):
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        v = (u[0]+dx, u[1]+dy)
        if v in light and v not in seen:
            seen.add(v)
            if v not in match or aug(match[v], seen):
                match[v] = u
                return True
    return False
size = sum(aug(u, set()) for u in dark)
ok(size == 16, size)
ok(len(cells)//2 == 17, "q5 distractor 17")

# extremal example: no finite set of positive integers (subset of 1..12) where each member
# is the sum of two other members
bad = 0
for mask in range(1, 1 << 12):
    s = [k+1 for k in range(12) if mask >> k & 1]
    if all(any(a + b == x for a, b in itertools.combinations([y for y in s if y != x], 2)) for x in s):
        bad += 1
ok(bad == 0, "extremal")
# invariance example: 7 lamps, each move flips exactly 2; can all 7 be on?
seen = {0}; frontier = [0]
while frontier:
    nxt = []
    for s in frontier:
        for i, j in itertools.combinations(range(7), 2):
            t = s ^ (1 << i) ^ (1 << j)
            if t not in seen: seen.add(t); nxt.append(t)
    frontier = nxt
ok((1 << 7) - 1 not in seen, "invariance lamps")
print(f"OK {n} checks")
