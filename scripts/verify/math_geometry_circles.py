"""Independent numeric checks for materi/math/geometry-circles.md (examples + Check your understanding)."""
import math

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1
def close(a, b, tol=1e-9): return abs(a - b) < tol
def dist(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])
def on(c, r, deg): return (c[0] + r*math.cos(math.radians(deg)), c[1] + r*math.sin(math.radians(deg)))
def angle(P, Q, R):  # angle at P in degrees
    u = (Q[0]-P[0], Q[1]-P[1]); v = (R[0]-P[0], R[1]-P[1])
    return math.degrees(math.acos((u[0]*v[0] + u[1]*v[1]) / (math.hypot(*u)*math.hypot(*v))))
def line_circle(P, d, c, r):
    """Intersections of line P + t*d (d unit) with circle; returns sorted t values."""
    f = (P[0]-c[0], P[1]-c[1]); b = f[0]*d[0] + f[1]*d[1]; cc = f[0]**2 + f[1]**2 - r*r
    disc = b*b - cc
    return sorted([-b - math.sqrt(disc), -b + math.sqrt(disc)])

# Example 1: smoke radius 5 centered at O, P is 13 away, PA = 9 -> chord AB inside the smoke
O = (0.0, 0.0); P = (13.0, 0.0); r = 5.0
# A: on circle with |PA| = 9 (take the upper intersection)
x = (r*r - 81 + 13*13) / 26; y = math.sqrt(r*r - x*x)
A = (x, y)
ok(close(dist(O, A), 5) and close(dist(P, A), 9), "A placed")
d = ((A[0]-P[0])/9, (A[1]-P[1])/9)
t1, t2 = line_circle(P, d, O, r)
ok(close(t1, 9), "near point at 9")
ok(close(t2, 16) and close(t2 - t1, 7), "PB = 16, AB = 7")
ok(close(t1*t2, 13**2 - 5**2), "power of a point = PO^2 - r^2 = 144")
ok(close(math.sqrt(13**2 - 5**2), 12), "tangent length 12")
# Example 2: cyclic quadrilateral ABCD, arc AC containing D is 140 degrees
c = (0.0, 0.0)
A, B, C, D = on(c, 1, 0), on(c, 1, 100), on(c, 1, 220), on(c, 1, 290)   # arc C->A via D is 140
ok(close(angle(D, A, C), 110), "angle ADC = 110")
ok(close(angle(B, A, C), 70), "angle ABC = 70 (distractor)")
ok(close(angle(D, A, C) + angle(B, A, C), 180), "opposite angles add to 180")
ok(close(angle(c, A, C), 140) or close(angle(c, A, C), 140.0), "central angle AOC = 140 on the D side")

# Q1: central 86 -> inscribed 43
c = (0.0, 0.0)
A, B = on(c, 1, 20), on(c, 1, 106)
ok(close(angle(c, A, B), 86), "central 86")
for deg in (150, 200, 250, 300):
    ok(close(angle(on(c, 1, deg), A, B), 43), f"inscribed angle from {deg} deg")
ok(close(90 - 43, 47) and close(180 - 43, 137) and close(2*86, 172), "q1 distractors")
# Q2: smoke radius 6, standing 10 from center: tangent line of sight
O = (0.0, 0.0); P = (10.0, 0.0); r = 6.0
found = []
N = 2000000
for i in range(N):
    T = on(O, r, 360*i/N)
    if abs((T[0]-P[0])*T[0] + (T[1]-P[1])*T[1]) < 2e-4:     # radius perpendicular to PT
        found.append(dist(P, T))
ok(len(found) >= 2 and all(abs(f - 8) < 1e-3 for f in found), found[:3])
ok(10 - 6 == 4 and 10 + 6 == 16, "q2 distractors 4 and 16")
# Q3: chords AB, CD cross at P; AP=4, PB=9, CP=2 -> PD
P = (0.0, 0.0); A, B, C = (-4.0, 0.0), (9.0, 0.0), (0.0, 2.0)
cx = (A[0] + B[0]) / 2
# center (cx, k): equidistant from A and C
k = (cx**2 + 0 - (A[0]-cx)**2 - 0) / 1.0   # placeholder, solved below numerically
best = None
for i in range(-200000, 200000):
    kk = i / 10000
    e = abs(math.hypot(cx - A[0], kk) - math.hypot(cx - C[0], kk - C[1]))
    if best is None or e < best[0]: best = (e, kk)
kc = best[1]; R = math.hypot(cx - A[0], kc)
ys = [kc + math.sqrt(R*R - cx*cx), kc - math.sqrt(R*R - cx*cx)]       # circle meets x = 0
ok(any(close(y, 2, 1e-3) for y in ys), "C is on the circle")
Dy = [y for y in ys if not close(y, 2, 1e-3)][0]
ok(abs(abs(Dy) - 18) < 1e-3, f"PD = {abs(Dy)}")
ok(4*9 == 2*18 and 4 + 9 == 13 and 4*9/ 6 == 6, "q3 power of a point and distractors")
# Q4: pizza, ABCD in order on circle, angle BAD = 112, angle ABC = 78 -> angle BCD
arcs = [80, 124, 100, 56]   # AB, BC, CD, DA
ok(sum(arcs) == 360, "arcs")
c = (0.0, 0.0); a0 = 0.0; angs = [a0]
for a in arcs[:-1]: angs.append(angs[-1] + a)
A, B, C, D = [on(c, 1, t) for t in angs]
ok(close(angle(A, B, D), 112) and close(angle(B, A, C), 78), "given angles realised")
ok(close(angle(C, B, D), 68), "q4 = 68")
ok(close(angle(D, A, C), 102), "distractor 102 = angle ADC")
# Q5: externally tangent circles, radii 9 and 4: common external tangent length
O1, O2 = (0.0, 0.0), (13.0, 0.0); r1, r2 = 9.0, 4.0
ok(close(dist(O1, O2), r1 + r2), "externally tangent")
nx = (r1 - r2) / 13; ny = math.sqrt(1 - nx*nx)
T1 = (O1[0] + r1*nx, O1[1] + r1*ny); T2 = (O2[0] + r2*nx, O2[1] + r2*ny)
tx, ty = T2[0] - T1[0], T2[1] - T1[1]
ok(close(tx*nx + ty*ny, 0), "T1T2 is perpendicular to both radii")
ok(close(math.hypot(tx, ty), 12), "q5 = 12")
ok(close(13**2 - 5**2, 144) and 13 - 8 == 5, "q5 distractors")
print(f"OK {n} checks")
