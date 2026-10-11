"""Independent numeric checks for materi/math/geometry-coordinate.md."""
import math
from fractions import Fraction as F

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1
def close(a, b, tol=1e-9): return abs(a - b) < tol
def lattice_area(P):
    """Area by Pick's theorem: A = I + B/2 - 1 (lattice polygon), counting points by brute force."""
    xs = [p[0] for p in P]; ys = [p[1] for p in P]
    def side(a, b, p): return (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0])
    # orient counterclockwise
    s = sum(P[i][0]*P[(i+1) % len(P)][1] - P[(i+1) % len(P)][0]*P[i][1] for i in range(len(P)))
    Q = P if s > 0 else P[::-1]
    I = Bd = 0
    for x in range(min(xs), max(xs)+1):
        for y in range(min(ys), max(ys)+1):
            sides = [side(Q[i], Q[(i+1) % len(Q)], (x, y)) for i in range(len(Q))]
            if all(v >= 0 for v in sides):
                if any(v == 0 for v in sides): Bd += 1
                else: I += 1
    return F(2*I + Bd - 2, 2)

# Example 1: line through A(1,2), B(7,10) meets x + 2y = 16 at P; find AP
A, B = (1, 2), (7, 10)
sols = [(x, y) for x in range(-30, 31) for y in range(-30, 31)
        if 4*x - 3*y + 2 == 0 and x + 2*y == 16]
ok(sols == [(4, 6)], sols)
ok(4*A[0] - 3*A[1] + 2 == 0 and 4*B[0] - 3*B[1] + 2 == 0, "both points on 4x-3y+2=0")
ok(close(math.dist(A, (4, 6)), 5) and close(math.dist(A, B), 10), "AP = 5, AB = 10")
ok(((A[0]+B[0])/2, (A[1]+B[1])/2) == (4, 6), "P is the midpoint")
ok(F(10-2, 7-1) == F(4, 3), "slope")
# Example 2: quadrilateral (1,1),(7,2),(6,6),(2,5) -> area 20
Q = [(1, 1), (7, 2), (6, 6), (2, 5)]
ok(lattice_area(Q) == 20, "Pick area")
sh = F(abs(sum(Q[i][0]*Q[(i+1) % 4][1] - Q[(i+1) % 4][0]*Q[i][1] for i in range(4))), 2)
ok(sh == 20, "shoelace")
ok(sum(Q[i][0]*Q[(i+1) % 4][1] for i in range(4)) == 76 and sum(Q[i][1]*Q[(i+1) % 4][0] for i in range(4)) == 36, "76 and 36")
ok(40 == 76 - 36, "distractor 40 forgets the half")
# circle in the picture
ok(all((x-3)**2 + (y-2)**2 == 25 for x, y in [(6, 6), (7, 5), (-2, 2), (8, 2), (3, 7), (3, -3)]), "points on picture circle")
ok(sorted(x for x in range(-10, 11) if (x-3)**2 + (2-2)**2 == 25) == [-2, 8], "y = 2 meets circle at 2 points")
# Q1: distance (-1,-2) to (4,10)
ok(close(math.dist((-1, -2), (4, 10)), 13), "q1")
ok(5 == 4 - (-1) and 12 == 10 - (-2) and 17 == 5 + 12 and 7 == 12 - 5, "q1 distractors")
# Q2: which point is exactly 5 from (3,2)
opts = {"A": (6, 6), "B": (1, 5), "C": (5, 4), "D": (7, 3), "E": (4, 6)}
on_circle = [k for k, p in opts.items() if (p[0]-3)**2 + (p[1]-2)**2 == 25]
ok(on_circle == ["A"], on_circle)
# Q3: through (2,-1), perpendicular to 3x + 2y = 6 -> y-intercept
m_given = F(-3, 2); m_perp = F(2, 3)
ok(m_given*m_perp == -1, "perpendicular")
b = F(-1) - m_perp*2; ok(b == F(-7, 3), "q3 y-intercept")
ok(F(-1) - m_given*2 == 2 and F(-1) - F(-2, 3)*2 == F(1, 3) and F(-1) - F(3, 2)*2 == -4, "q3 distractors (parallel, wrong sign, no reciprocal)")
# Q4: y = x + 1, y = -x + 5 and the x-axis: area (numeric grid sum)
N = 3000; tot = 0.0
for i in range(N):
    x = -1 + 6*(i + 0.5)/N
    h = min(x + 1, 5 - x)
    if h > 0: tot += h*(6/N)
ok(abs(tot - 9) < 1e-3, tot)
ok(F(1, 2)*6*3 == 9 and 6*3 == 18, "q4 and distractor 18")
# Q5: pool corners (1,1), (9,3), (5,8)
T = [(1, 1), (9, 3), (5, 8)]
ok(lattice_area(T) == 24, "Pick area 24")
ok(F(abs(sum(T[i][0]*T[(i+1) % 3][1] - T[(i+1) % 3][0]*T[i][1] for i in range(3))), 2) == 24, "shoelace 24")
ok(48 == 2*24, "distractor 48 forgets the half")
print(f"OK {n} checks")
