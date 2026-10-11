"""Independent checks for materi/math/algebra-polynomials.md (examples + Cek Paham)."""
from fractions import Fraction
from math import comb
import itertools

n = 0
def ok(c, msg):
    global n
    assert c, msg
    n += 1

# Example 1: roots of x^3 - 7x^2 + 14x - 8 -> r^2+s^2+t^2
roots = [r for r in range(-20, 21) if r**3 - 7*r**2 + 14*r - 8 == 0]
ok(sorted(roots) == [1, 2, 4], roots)
ok(sum(r*r for r in roots) == 21, "ex1 value")
ok(7**2 - 2*14 == 21, "ex1 vieta route")
# Example 2: coefficient of x^4 in (x+2)^6
ok(comb(6, 4) * 2**2 == 60, "ex2")

# Q1: remainder of x^3-3x^2+2x+5 divided by x-3
P = lambda x: x**3 - 3*x**2 + 2*x + 5
ok(P(3) == 11, "q1")
ok(P(1) == 5 and 27 - 27 + 6 == 6, "q1 distractors are plausible mistakes")
# Q2: area x^2-7x+10, length x-2, x=9 -> width
x = 9
ok((x*x - 7*x + 10) / (x - 2) == 4 and (x - 5) == 4, "q2")
ok(x*x - 7*x + 10 == 28 and x - 2 == 7, "q2 numbers")
# Q3: possible rational roots of 2x^3-3x^2+5x-6 (p | 6, q | 2)
poss = set()
for p in (1, 2, 3, 6):
    for q in (1, 2):
        poss |= {Fraction(p, q), Fraction(-p, q)}
ok(Fraction(2, 3) not in poss, "q3 answer 2/3 must be impossible")
ok(all(c in poss for c in (Fraction(3, 2), Fraction(1, 2), Fraction(6), Fraction(-3))), "q3 others possible")
# Q4: coefficient of x^2 in (x+3)^5
ok(comb(5, 2) * 3**3 == 270, "q4")
ok(comb(5, 2) * 3**2 == 90, "q4 distractor 90 = wrong exponent")
# Q5: 2x^2-10x+12=0 -> 1/p+1/q
rts = [Fraction(r) for r in range(-20, 21) if 2*r*r - 10*r + 12 == 0]
ok(sorted(rts) == [2, 3], rts)
ok(sum(1/r for r in rts) == Fraction(5, 6) and Fraction(10, 2) / Fraction(12, 2) == Fraction(5, 6), "q5")
print(f"OK {n} checks")
