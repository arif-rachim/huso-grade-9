"""Independent numeric checks for materi/math/geometry-transformations.md."""
import math
from fractions import Fraction as F

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1
def close(a, b, tol=1e-9): return abs(a - b) < tol
def rot(p, deg, c=(0, 0)):
    a = math.radians(deg); x, y = p[0]-c[0], p[1]-c[1]
    q = (c[0] + x*math.cos(a) - y*math.sin(a), c[1] + x*math.sin(a) + y*math.cos(a))
    return (round(q[0], 9), round(q[1], 9))
def refl_line(p, A, B):
    """Reflect p in the line through A and B (general formula via projection)."""
    dx, dy = B[0]-A[0], B[1]-A[1]; t = ((p[0]-A[0])*dx + (p[1]-A[1])*dy) / (dx*dx + dy*dy)
    f = (A[0] + t*dx, A[1] + t*dy)
    return (round(2*f[0] - p[0], 9), round(2*f[1] - p[1], 9))
def trans(p, v): return (p[0]+v[0], p[1]+v[1])
def dil(p, k, c=(0, 0)): return (c[0] + k*(p[0]-c[0]), c[1] + k*(p[1]-c[1]))
def area(P): return abs(sum(P[i][0]*P[(i+1) % len(P)][1] - P[(i+1) % len(P)][0]*P[i][1] for i in range(len(P)))) / 2

# sanity: the rules in the text
ok(rot((3, 1), 90) == (-1, 3) and rot((3, 1), 180) == (-3, -1) and rot((3, 1), 270) == (1, -3), "rotation rules")
ok(refl_line((3, 1), (0, 0), (1, 1)) == (1, 3), "reflect in y=x swaps")
ok(refl_line((3, 1), (0, 0), (1, -1)) == (-1, -3), "reflect in y=-x")
ok(refl_line((3, 1), (0, 0), (1, 0)) == (3, -1) and refl_line((3, 1), (0, 0), (0, 1)) == (-3, 1), "axes")
# the picture: triangle (1,1),(2,1),(1,2)
T = [(1, 1), (2, 1), (1, 2)]
ok([trans(p, (2, 3)) for p in T] == [(3, 4), (4, 4), (3, 5)], "translation in picture")
ok([dil(p, 2) for p in T] == [(2, 2), (4, 2), (2, 4)] and close(area([dil(p, 2) for p in T]), 4*area(T)), "dilation in picture")

# Example 1: P(3,-2): rotate 90 ccw, reflect in y=x, translate (4,1)
P = (3, -2)
Q = rot(P, 90); ok(Q == (2, 3), "step 1")
Q = refl_line(Q, (0, 0), (1, 1)); ok(Q == (3, 2), "step 2")
Q = trans(Q, (4, 1)); ok(Q == (7, 3), "answer (7,3)")
# distractors
R = trans(P, (4, 1)); R = rot(R, 90); R = refl_line(R, (0, 0), (1, 1)); ok(R == (7, 1), "wrong order gives (7,1)")
R = rot(P, -90); R = refl_line(R, (0, 0), (1, 1)); R = trans(R, (4, 1)); ok(R == (1, -1), "clockwise gives (1,-1)")
R = rot(P, 90); R = refl_line(R, (0, 0), (0, 1)); R = trans(R, (4, 1)); ok(R == (2, 4), "reflect in y-axis gives (2,4)")
ok((3, 7) != (7, 3) and (3, 7) not in [(7, 1), (1, -1), (2, 4)], "(3,7) is the swapped answer")
# Example 2: dilation center (2,1), factor 3, A(4,3)
A = (4, 3); A2 = dil(A, 3, (2, 1)); ok(A2 == (8, 7), "A'")
ok(close(math.dist(A, A2), 4*math.sqrt(2)), "AA' = 4 sqrt 2")
ok(close(math.dist((2, 1), A), 2*math.sqrt(2)) and close(math.dist((2, 1), A2), 6*math.sqrt(2)), "distractors 2sqrt2, 6sqrt2")
# Q1: (4,-7) reflected in y=x
ok(refl_line((4, -7), (0, 0), (1, 1)) == (-7, 4), "q1")
ok(refl_line((4, -7), (0, 0), (0, 1)) == (-4, -7) or True, "")
ok(refl_line((4, -7), (0, 0), (0, 1)) == (-4, -7), "reflect in y-axis (-4,-7)")
ok(refl_line((4, -7), (0, 0), (1, 0)) == (4, 7), "x-axis (4,7)")
ok(refl_line((4, -7), (0, 0), (1, -1)) == (7, -4), "y=-x (7,-4)")
ok(rot((4, -7), 180) == (-4, 7), "180 deg (-4,7)")
# Q2: wall x = 10, swimmer start (2,5)
W = refl_line((2, 5), (10, 0), (10, 1)); ok(W == (18, 5), "q2")
ok(refl_line((2, 5), (0, 0), (0, 1)) == (-2, 5) and refl_line((2, 5), (0, 10), (1, 10)) == (2, 15), "q2 distractors")
# Q3: rotate (2,-3) 90 degrees clockwise about the origin
ok(rot((2, -3), -90) == (-3, -2), "q3")
ok(rot((2, -3), 90) == (3, 2) and rot((2, -3), 180) == (-2, 3), "q3 distractors")
# Q4: 4x3 card enlarged by 2.5
card = [(0, 0), (4, 0), (4, 3), (0, 3)]
ok(close(area([dil(p, 2.5) for p in card]), 75), "q4")
ok(close(12*2.5, 30) and close(12*5, 60), "q4 distractors")
# Q5: reflect (1,2) in x=3 then x=7
p = refl_line((1, 2), (3, 0), (3, 1)); ok(p == (5, 2), "after first")
p = refl_line(p, (7, 0), (7, 1)); ok(p == (9, 2), "q5")
ok(trans((1, 2), (2*(7-3), 0)) == (9, 2), "two parallel mirrors = translation by 2*gap")
print(f"OK {n} checks")
