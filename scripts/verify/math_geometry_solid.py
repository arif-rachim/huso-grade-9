"""Independent numeric checks for materi/math/geometry-solid.md (slicing / vertex coordinates, not the textbook formulas)."""
import math

n = 0
def ok(c, msg=""):
    global n
    assert c, msg
    n += 1
def close(a, b, tol=1e-6): return abs(a - b) <= tol * max(1, abs(b))
def integrate(f, a, b, N=200000):
    h = (b - a) / N
    return sum(f(a + (i + 0.5)*h) for i in range(N)) * h
def cone_volume(r, h):       # stack of thin disks
    return integrate(lambda z: math.pi*(r*(1 - z/h))**2, 0, h)
def cone_lateral(r, h):      # surface of revolution: 2*pi*radius * slant element
    l = math.hypot(r, h)
    return integrate(lambda z: 2*math.pi*(r*(1 - z/h)) * (l/h), 0, h)
def sphere_volume(r):
    return integrate(lambda z: math.pi*(r*r - z*z), -r, r)
def sphere_area(r):          # slices: 2*pi*sqrt(r^2-z^2) * (r/sqrt(r^2-z^2)) dz
    return integrate(lambda z: 2*math.pi*r, -r, r)
def tri_area3(a, b, c):
    u = [b[i]-a[i] for i in range(3)]; v = [c[i]-a[i] for i in range(3)]
    w = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    return 0.5*math.sqrt(sum(x*x for x in w))

# Example 1: cone r=6, h=8 poured into a cylinder of radius 4
V = cone_volume(6, 8)
ok(close(V, 96*math.pi), "cone volume 96 pi")
ok(close(V / (math.pi*16), 6), "water height 6")
ok(close(3*V / (math.pi*16), 18), "distractor 18 forgets the 1/3")
# Example 2: sphere inside a cylinder (r = 1, height 2)
ok(close(sphere_volume(1) / (math.pi*1*2), 2/3), "ratio 2/3")
# cone r=3,h=4: slant 5, total surface 24 pi
ok(close(cone_lateral(3, 4), 15*math.pi) and close(cone_lateral(3, 4) + math.pi*9, 24*math.pi), "cone SA 24 pi")
# Q1: box 3 x 4 x 5, all six faces
faces = [3*4]*2 + [3*5]*2 + [4*5]*2
ok(sum(faces) == 94 and 3*4*5 == 60 and 2*47 == 94 and 4*sum(faces) // 2 == 188, "q1")
# Q2: cone r=3, h=4
ok(close(cone_volume(3, 4), 12*math.pi), "q2")
ok(close(3*cone_volume(3, 4), 36*math.pi) and close(math.pi*3*5, 15*math.pi) and close(math.pi*3*16/3, 16*math.pi), "q2 distractors")
# Q3: sphere with surface area 36 pi -> volume
def sphere_area_true(r):    # surface of revolution of y = sqrt(r^2 - z^2): 2*pi*y*sqrt(1 + y'^2)
    return integrate(lambda z: 2*math.pi*math.sqrt(r*r - z*z)*math.sqrt(1 + z*z/(r*r - z*z)), -r, r, 400000)
ok(abs(sphere_area_true(3) - 36*math.pi) < 1e-3, "surface area of the r = 3 sphere is 36 pi")
ok(close(sphere_volume(3), 36*math.pi), "q3 volume")
ok(close(4*math.pi*27, 108*math.pi), "q3 distractor 108 pi (no 1/3)")
# Q4: scale model 1:10 holds 2 L
ok(10**3 * 2 == 2000 and 10*2 == 20 and 10**2*2 == 200, "q4")
# Q5: square pyramid, base 6, height 4 (coordinates)
apex = (0, 0, 4); P = [(3, 3, 0), (-3, 3, 0), (-3, -3, 0), (3, -3, 0)]
lat = sum(tri_area3(apex, P[i], P[(i+1) % 4]) for i in range(4))
ok(close(lat, 60), "lateral area 60")
ok(close(lat + 36, 96), "q5 total 96")
ok(close(36 + 4*0.5*6*4, 84) and close(36*4/3, 48), "q5 distractors 84 (height not slant), 48 (volume)")
print(f"OK {n} checks")
