"""Independent numeric checks for materi/math/geometry-triangles.md (examples + Check your understanding)."""
import math
from fractions import Fraction

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1
def close(a, b, tol=1e-9): return abs(a - b) < tol
def dist(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])
def area(*P):
    return abs(sum(P[i][0]*P[(i+1) % len(P)][1] - P[(i+1) % len(P)][0]*P[i][1] for i in range(len(P)))) / 2
def place(a, b, c):
    """Triangle with BC = a (on the x-axis), CA = b, AB = c. Returns A, B, C."""
    B = (0.0, 0.0); C = (float(a), 0.0)
    x = (c*c - b*b + a*a) / (2*a); y = math.sqrt(c*c - x*x)
    return (x, y), B, C
def dist_to_line(P, X, Y):
    return abs((Y[0]-X[0])*(X[1]-P[1]) - (X[0]-P[0])*(Y[1]-X[1])) / dist(X, Y)
def circumcenter(A, B, C):
    ax, ay = A; bx, by = B; cx, cy = C
    d = 2*(ax*(by-cy) + bx*(cy-ay) + cx*(ay-by))
    return (((ax*ax+ay*ay)*(by-cy) + (bx*bx+by*by)*(cy-ay) + (cx*cx+cy*cy)*(ay-by)) / d,
            ((ax*ax+ay*ay)*(cx-bx) + (bx*bx+by*by)*(ax-cx) + (cx*cx+cy*cy)*(bx-ax)) / d)

# Example 1: pool 13-14-15, point equally far from all three sides (brute force grid search)
A, B, C = place(14, 15, 13)   # BC=14, CA=15, AB=13
K = area(A, B, C)
ok(close(K, 84), "area 84")
best = None
steps = 800
for i in range(1, steps):
    for j in range(1, steps):
        P = (14*i/steps, 15*j/steps)
        # inside test
        if area(P, B, C) + area(A, P, C) + area(A, B, P) > K + 1e-9: continue
        m = min(dist_to_line(P, A, B), dist_to_line(P, B, C), dist_to_line(P, A, C))
        if best is None or m > best[0]: best = (m, P)
ok(abs(best[0] - 4) < 0.02, f"max inscribed radius ~4, got {best[0]}")
s = (13+14+15)/2
ok(close(math.sqrt(s*(s-13)*(s-14)*(s-15)), 84), "Heron")
ok(close(K / s, 4), "r = K/s")
ok(close(13*14*15/(4*K), 65/8), "R of 13-14-15")

# Example 2: angle bisector, AB=6, AC=10, BC=12 -> BD
A, B, C = place(12, 10, 6)
def ang(P, Q, R_):   # angle at P between Q and R_
    u = (Q[0]-P[0], Q[1]-P[1]); v = (R_[0]-P[0], R_[1]-P[1])
    return math.acos((u[0]*v[0] + u[1]*v[1]) / (math.hypot(*u)*math.hypot(*v)))
lo, hi = 0.0, 12.0
for _ in range(100):
    mid = (lo+hi)/2; D = (mid, 0.0)
    if ang(A, B, D) < ang(A, D, C): lo = mid
    else: hi = mid
ok(abs(lo - 4.5) < 1e-9, f"BD = {lo}")
ok(abs(12*6/16 - 4.5) < 1e-12 and abs(12*10/16 - 7.5) < 1e-12, "BD, DC by ratio")

# Q1: 30-60-90 with hypotenuse 12: long leg
leg_long = 12*math.cos(math.radians(30)); leg_short = 12*math.sin(math.radians(30))
ok(close(leg_short, 6) and close(leg_long, 6*math.sqrt(3)), "q1")
ok(not close(leg_long, 4*math.sqrt(3)) and not close(leg_long, 6*math.sqrt(2)), "q1 distractors differ")
ok(close(12/math.sqrt(3), 4*math.sqrt(3)), "q1 distractor 4*sqrt3 = 12/sqrt3 (wrong ratio)")
# Q2: 5-12-13 triangle, circle through all corners
A, B, C = (0, 0), (12, 0), (0, 5)
ok(close(dist(B, C), 13), "5-12-13 right triangle")
O = circumcenter(A, B, C)
ok(close(dist(O, A), 6.5) and close(dist(O, B), 6.5) and close(dist(O, C), 6.5), "q2 circumradius 13/2")
ok(close(13*12*5/(4*area(A, B, C)), 6.5), "q2 R=abc/4K")
# Q3: sides 6, 25, 29
A, B, C = place(29, 25, 6)   # BC=29, CA=25, AB=6
ok(close(area(A, B, C), 60), "q3 area 60")
ok(dist(A, B) > 0 and close(dist(A, B), 6) and close(dist(A, C), 25), "q3 placement")
s = 30; ok(close(math.sqrt(s*(s-6)*(s-25)*(s-29)), 60), "q3 Heron")
ok(close(0.5*6*25, 75) and close(0.5*29*6, 87) , "q3 distractors (wrong-height products)")
# Q4: DE || BC, AD=4, DB=6, area ADE = 8 -> area ABC
A, B, C = (3.0, 10.0), (0.0, 0.0), (10.0, 0.0)
D = (A[0] + 0.4*(B[0]-A[0]), A[1] + 0.4*(B[1]-A[1])); E = (A[0] + 0.4*(C[0]-A[0]), A[1] + 0.4*(C[1]-A[1]))
ok(close(dist(A, D)/dist(A, B), 0.4), "AD/AB = 4/10")
ok(close(area(A, D, E) / area(A, B, C), 0.16), "area ratio 4/25")
ok(close(8 / 0.16, 50), "q4 = 50")
ok(close(8*2.5, 20) and close(8*5, 40), "q4 distractors: linear ratio / wrong factor")
# Q5: A(0,0) B(9,0) C(0,12): centroid distance to A
A, B, C = (0, 0), (9, 0), (0, 12)
G = ((A[0]+B[0]+C[0])/3, (A[1]+B[1]+C[1])/3)
ok(G == (3, 4) and close(dist(G, A), 5), "q5")
O = circumcenter(A, B, C)
ok(close(O[0], 4.5) and close(O[1], 6) and close(dist(O, A), 7.5), "q5 distractor: circumcenter distance 7.5")
a, b, c = dist(B, C), dist(A, C), dist(A, B)
I = ((a*A[0] + b*B[0] + c*C[0])/(a+b+c), (a*A[1] + b*B[1] + c*C[1])/(a+b+c))
ok(close(I[0], 3) and close(I[1], 3), "incenter (3,3)")
print(f"OK {n} checks")
