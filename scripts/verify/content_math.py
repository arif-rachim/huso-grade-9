"""Independent solver for content/questions/math.json (issue #22).

Every question below is written together with a computation that recomputes its correct
answer FROM SCRATCH (brute force, exact fractions, simulation, coordinates), never from the
formula the explanation quotes. The correct choice text comes out of that computation.

  python3 scripts/verify/content_math.py            # recompute, compare with the JSON, exit 1 on any mismatch
  python3 scripts/verify/content_math.py --write    # (re)generate content/questions/math.json from this file
"""
import itertools
import json
import math
import random
import sys
from fractions import Fraction as F
from math import comb, factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "content" / "questions" / "math.json"

QS = []


def q(sub, d, stem, correct, wrong, expl, ev=None, visual=None):
    correct = str(correct)
    wrong = [str(w) for w in wrong]
    assert len(wrong) == 4, stem
    assert correct not in wrong and len(set(wrong)) == 4, (stem, correct, wrong)
    QS.append(dict(sub=sub, d=d, stem=stem, correct=correct, wrong=wrong, expl=expl, ev=ev, visual=visual))


def fr(x):
    x = F(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def pt(x, y):
    return f"({fr(x)}, {fr(y)})".replace("-", "−")


def sqrtstr(n):
    r = math.isqrt(n)
    return str(r) if r * r == n else f"√{n}"


# ---------------------------------------------------------------- polynomials
S = "math.algebra.polynomials"
T = lambda x: x**3 - 2 * x**2 + 5 * x - 7
q(S, 1, "A coach models a swimmer's lap time (in seconds) after x weeks as T(x) = x³ − 2x² + 5x − 7. "
        "What is the remainder when T(x) is divided by (x − 2)?",
  T(2), [T(-2), T(0), T(3), T(1)],
  "Remainder theorem: the remainder on division by (x − 2) is T(2) = 8 − 8 + 10 − 7 = 3. "
  "The other choices are T(−2), T(0), T(3) and T(1): wrong inputs.", "content/math/polynomials-area-model.svg")

roots_sum = F(sum([(10 + math.sqrt(10**2 - 4 * 2 * 7)) / 4, (10 - math.sqrt(10**2 - 4 * 2 * 7)) / 4])).limit_denominator(1000)
q(S, 1, "What is the sum of the two roots of 2x² − 10x + 7 = 0?",
  fr(roots_sum), ["−5", "7/2", "10", "−7/2"],
  "Vieta: the sum of the roots is −b/a = 10/2 = 5. The product 7/2 is not what was asked, and the "
  "sign of −b/a is easy to flip.")


def rational_candidates(const, lead, cand):
    n, dn = cand.numerator, cand.denominator
    return const % abs(n) == 0 and lead % dn == 0


cands = {"3/2": F(3, 2), "6": F(6), "1/2": F(1, 2), "2/3": F(2, 3), "−3": F(-3)}
bad = [k for k, v in cands.items() if not rational_candidates(6, 2, v)]
assert bad == ["2/3"]
q(S, 1, "By the rational root theorem, which of these numbers can NOT be a root of 2x³ − 5x² + x − 6 = 0?",
  "2/3", ["3/2", "6", "1/2", "−3"],
  "A rational root m/n (lowest terms) needs m to divide the constant term 6 and n to divide the leading "
  "coefficient 2. For 2/3 the denominator 3 does not divide 2, so it is impossible.")

B = lambda x: x**3 - 7 * x + 6
pos = [x for x in range(1, 60) if B(x) == 0]
q(S, 2, "In a made-up Valorant economy model, the bonus after round x is B(x) = x³ − 7x + 6 (in hundreds of credits). "
        "Find the sum of all positive whole-number rounds x at which B(x) = 0.",
  sum(pos), [0, 6, -3, 2],
  "B(x) = (x − 1)(x − 2)(x + 3), so the roots are 1, 2 and −3. Only 1 and 2 are positive: 1 + 2 = 3. "
  "The sum of all three roots is 0 (Vieta), a common trap.")

ks = [k for k in range(-30, 31) if 27 - 9 * k + 3 + 6 == 0]
assert ks == [4] and all((x**3 - ks[0] * x**2 + x + 6) % (x - 3) == 0 for x in [4, 5, 6, 7])
q(S, 2, "For which value of k is (x − 3) a factor of x³ − kx² + x + 6?",
  ks[0], [-4, 2, 6, 12],
  "(x − 3) is a factor exactly when the polynomial is 0 at x = 3: 27 − 9k + 3 + 6 = 36 − 9k = 0, so k = 4.")

pq = [(p, 34 - p) for p in range(1, 34) if p * (34 - p) == 240 and p < 34 - p]
diag = math.hypot(*pq[0])
q(S, 2, "The side lengths (in cm) of a rectangular baking tray are the two roots of x² − 34x + 240 = 0. "
        "How long is the diagonal of the tray?",
  f"{round(diag)} cm", ["24 cm", "28 cm", "34 cm", "√240 cm"],
  "Vieta: p + q = 34, pq = 240. Then p² + q² = 34² − 2·240 = 676, so the diagonal is √676 = 26 cm "
  "(the sides are 10 and 24).")

sols = [(a, b) for a in range(-20, 21) for b in range(-20, 21) if 1 + a + b == 5 and -1 - a + b == 1]
assert sols == [(1, 3)]
a_, b_ = sols[0]
q(S, 3, "P(x) = x³ + ax + b leaves remainder 5 when divided by (x − 1) and remainder 1 when divided by (x + 1). "
        "What is P(2)?",
  2**3 + a_ * 2 + b_, [11, 15, 9, 7],
  "P(1) = 1 + a + b = 5 and P(−1) = −1 − a + b = 1. Adding: 2b = 6, so b = 3 and a = 1. "
  "Then P(2) = 8 + 2 + 3 = 13.")

coef = {}
for k in range(7):
    e = 6 - 2 * k
    coef[e] = coef.get(e, 0) + comb(6, k) * 2**k
q(S, 3, "What is the constant term in the expansion of (x + 2/x)⁶?",
  coef[0], [20, 64, 80, 120],
  "The general term is C(6,k)·x⁶⁻ᵏ·(2/x)ᵏ = C(6,k)·2ᵏ·x⁶⁻²ᵏ. The power of x is 0 when k = 3, "
  "giving C(6,3)·2³ = 20·8 = 160.", "content/math/pascal-triangle.svg")

# ---------------------------------------------------------------- sequences
S = "math.algebra.sequences"
q(S, 1, "At swim practice you swim n laps of 50 m on day n, for the first 12 days (day 1: 1 lap, day 2: 2 laps, and so on). "
        "How many meters do you swim in total?",
  sum(50 * n for n in range(1, 13)), [600, 1950, 3000, 7800],
  "Total laps = 1 + 2 + … + 12 = 12·13/2 = 78. Then 78 × 50 m = 3900 m.", "content/math/sequences-arith-geom.svg")

x = 5
for _ in range(6):
    x *= 2
q(S, 1, "A baker starts a sourdough starter at 5 g. It doubles in mass every hour. How many grams after 6 hours?",
  x, [30, 160, 315, 640],
  "Geometric growth: 5 · 2⁶ = 5 · 64 = 320 g. (315 would be the total of the amounts added, "
  "which is a different question.)")

a1, d = 7, 4
seq = [a1]
while len(seq) < 20:
    seq.append(seq[-1] + d)
q(S, 1, "An arithmetic sequence starts 7, 11, 15, 19, … What is its 20th term?",
  seq[-1], [79, 80, 87, 91],
  "aₙ = a₁ + (n − 1)d = 7 + 19·4 = 83. Using 20·4 (87) is the classic off-by-one slip.")

q(S, 2, "What is 3 + 6 + 12 + 24 + … (a geometric series with 8 terms)?",
  sum(3 * 2**i for i in range(8)), [381, 768, 1020, 1533],
  "Sₙ = a(rⁿ − 1)/(r − 1) = 3(2⁸ − 1)/1 = 3·255 = 765.", "content/math/sequences-arith-geom.svg")

tot = F(0)
t = F(800)
for _ in range(200):
    tot += t
    t /= 2
inf = F(800) / (1 - F(1, 2))
assert abs(float(inf - tot)) < 1e-9
q(S, 2, "In a made-up Valorant economy, your round bonuses are 800, 400, 200, 100, … credits, each half of the previous one. "
        "If the pattern went on forever, what would the total be?",
  fr(inf), [800, 1000, 1200, 3200],
  "Infinite geometric series with |r| < 1: a/(1 − r) = 800/(1 − ½) = 1600.")

tel = sum(F(1, k * (k + 1)) for k in range(1, 21))
q(S, 2, "What is 1/(1·2) + 1/(2·3) + 1/(3·4) + … + 1/(20·21)?",
  fr(tel), ["19/20", "21/20", "1/21", "40/41"],
  "Write 1/(k(k+1)) = 1/k − 1/(k+1). Everything cancels except 1 − 1/21 = 20/21.",
  "content/math/sequences-telescoping.svg")

Sn = lambda n: n * n + 3 * n
q(S, 3, "The sum of the first n terms of a sequence is Sₙ = n² + 3n. What is the 10th term?",
  Sn(10) - Sn(9), [23, 19, 108, 130],
  "a₁₀ = S₁₀ − S₉ = 130 − 108 = 22. (130 is the sum of ten terms, not the tenth term.)")

val = sum(1 / (math.sqrt(k) + math.sqrt(k + 1)) for k in range(1, 25))
assert abs(val - 4) < 1e-9
q(S, 3, "What is the value of 1/(√1 + √2) + 1/(√2 + √3) + … + 1/(√24 + √25)?",
  round(val), [3, 5, 24, "√24"],
  "Multiply each term by its conjugate: 1/(√k + √(k+1)) = √(k+1) − √k. The sum telescopes to √25 − √1 = 4.",
  "content/math/sequences-telescoping.svg")

# ---------------------------------------------------------------- inequalities
S = "math.algebra.inequalities"
grid = [i / 100 for i in range(-1000, 2001)]
m = min(t * t - 6 * t + 11 for t in grid)
q(S, 1, "An oven's temperature error (in degrees squared) is modeled as D(t) = t² − 6t + 11 for t minutes after preheating. "
        "What is the smallest possible value of D(t)?",
  round(m), [0, -2, 5, 11],
  "Complete the square: t² − 6t + 11 = (t − 3)² + 2 ≥ 2, because a square is never negative. "
  "Equality at t = 3.")

m = min(x + 16 / x for x in (i / 1000 for i in range(100, 40000)))
q(S, 1, "For x > 0, what is the smallest possible value of x + 16/x?",
  round(m), [4, 16, 17, 20],
  "AM-GM: x + 16/x ≥ 2√(x · 16/x) = 2·4 = 8, with equality when x = 16/x, i.e. x = 4.")

cnt = sum(1 for x in range(1, 100) if x + 5 > 9 and x + 9 > 5 and 5 + 9 > x)
q(S, 1, "Two sides of a triangle are 5 and 9. How many whole-number lengths are possible for the third side?",
  cnt, [4, 8, 10, 14],
  "Triangle inequality: 9 − 5 < x < 9 + 5, so 4 < x < 14, giving x = 5, 6, …, 13: nine values.",
  "content/math/inequalities-triangle-sticks.svg")

best = max(w * (20 - w) for w in range(1, 20))
q(S, 2, "You rope off a rectangular kids' paddling area in the pool using exactly 40 m of rope around all four sides. "
        "What is the largest possible area, in m²?",
  best, [80, 99, 120, 200],
  "Width w, length 20 − w, area w(20 − w). By AM-GM this is at most ((w + 20 − w)/2)² = 100, "
  "reached by the 10 m × 10 m square.", "content/math/inequalities-rim-area.svg")

hm = F(2 * 4 * 12, 4 + 12)
q(S, 2, "What is the harmonic mean 2ab/(a + b) of 4 and 12?",
  fr(hm), [4, 8, 10, "√48"],
  "2·4·12/(4 + 12) = 96/16 = 6. Check the order HM ≤ GM ≤ AM: 6 ≤ √48 ≈ 6.93 ≤ 8.")

xmax = max(x for x in range(1, 100) if 6 + 11 > x and 6 + x > 11 and 11 + x > 6)
q(S, 2, "On a Valorant map, a triangular loop is made from three corridors of lengths 6 m, 11 m and x m, where x is a whole number. "
        "What is the greatest possible x?",
  xmax, [5, 15, 17, 18],
  "Need 11 − 6 < x < 11 + 6, i.e. 5 < x < 17. The greatest whole number is 16 (17 would make the corridors collapse into a straight line).")

mn = min(1 / a + 1 / (1 - a) for a in (i / 10000 for i in range(1, 10000)))
q(S, 3, "Positive numbers a and b satisfy a + b = 1. What is the smallest possible value of 1/a + 1/b?",
  round(mn), [1, 2, 5, 8],
  "(a + b)(1/a + 1/b) ≥ (by AM-GM or Cauchy) 4, and a + b = 1, so 1/a + 1/b ≥ 4, with equality at a = b = ½.")

mn = min(4 * (36 / y) + 9 * y for y in (i / 1000 for i in range(100, 30000)))
q(S, 3, "Positive numbers x and y satisfy xy = 36. What is the smallest possible value of 4x + 9y?",
  round(mn), [36, 78, 90, 144],
  "AM-GM: 4x + 9y ≥ 2√(4x·9y) = 2√(36·36) = 72. Equality when 4x = 9y, i.e. x = 9 and y = 4.")

# ---------------------------------------------------------------- functions
S = "math.algebra.functions"
nb = sum(1 for p in itertools.permutations(range(4)))
q(S, 1, "Four swimmers must each get their own lane in a 4-lane heat (a bijection from swimmers to lanes). In how many ways can the lanes be assigned?",
  nb, [4, 12, 16, 256],
  "A bijection matches each swimmer to a different lane: 4·3·2·1 = 24. (256 = 4⁴ counts all functions, "
  "including ones where two swimmers share a lane.)", "content/math/functions-who-sits-where.svg")

q(S, 1, "What is ⌊−2.3⌋ + ⌈2.3⌉?",
  math.floor(-2.3) + math.ceil(2.3), [-1, 1, -2, 2],
  "⌊−2.3⌋ is the greatest integer ≤ −2.3, which is −3 (not −2). ⌈2.3⌉ = 3. The sum is 0.",
  "content/math/functions-floor-ceiling.svg")

v = math.sin(math.radians(60)) * math.cos(math.radians(30))
assert abs(v - 0.75) < 1e-12
q(S, 1, "What is sin 60° · cos 30°?",
  "3/4", ["√3/4", "1/2", "√3/2", "1"],
  "sin 60° = cos 30° = √3/2, so the product is (√3/2)² = 3/4.")

# solve 2f(x) + f(1-x) = x  at x=0 and x=1:  2a + b = 0 ; 2b + a = 1   (a=f(0), b=f(1))
a_, b_ = None, None
for A_ in range(-30, 31):
    for den in (3,):
        for B_ in range(-30, 31):
            fa, fb = F(A_, den), F(B_, den)
            if 2 * fa + fb == 0 and 2 * fb + fa == 1:
                a_, b_ = fa, fb
q(S, 2, "A function satisfies 2f(x) + f(1 − x) = x for every real x. What is f(1)?",
  fr(b_), ["1/3", "1", "−1/3", "2"],
  "Put x = 0: 2f(0) + f(1) = 0. Put x = 1: 2f(1) + f(0) = 1. From the first, f(1) = −2f(0); "
  "substitute: −4f(0) + f(0) = 1, so f(0) = −1/3 and f(1) = 2/3.")

fs = [lambda x: x * x + 1, lambda x: x**3, lambda x: x**4 - x * x, lambda x: x + 1, lambda x: abs(x), lambda x: x**5 + x]
ev_ = sum(1 for f in fs if all(f(-t) == f(t) for t in range(1, 8)))
q(S, 2, "How many of these six functions are even? x² + 1,  x³,  x⁴ − x²,  x + 1,  |x|,  x⁵ + x",
  ev_, [1, 2, 4, 5],
  "Even means f(−x) = f(x): x² + 1, x⁴ − x² and |x| are even (3). x³ and x⁵ + x are odd, and x + 1 is neither.",
  "content/math/functions-even-odd.svg")

pop, h = 1000, 0
while pop < 64000:
    pop *= 2
    h += 0.5
q(S, 2, "A yeast culture of 1000 cells doubles every 30 minutes. After how many hours does it first reach 64 000 cells?",
  f"{h:g}", ["1.5", "2", "6", "12"],
  "64 000 = 1000 · 2⁶, so it takes 6 doublings. At 30 minutes each, that is 3 hours "
  "(equivalently log₂ 64 = 6 doublings).")

surj = 0
for f_ in itertools.product(range(3), repeat=4):
    if set(f_) == {0, 1, 2}:
        surj += 1
q(S, 3, "How many functions from {1, 2, 3, 4} onto {a, b, c} are surjective (every one of a, b, c is hit at least once)?",
  surj, [6, 18, 24, 81],
  "All functions: 3⁴ = 81. Subtract those missing at least one value: 3·2⁴ − 3·1⁴ = 45 (inclusion-exclusion). "
  "81 − 45 = 36.")

tot = sum(k // 3 for k in range(1, 21))
q(S, 3, "In a made-up Valorant mode your shield bonus after round k is ⌊k/3⌋ points. What is the sum of the bonuses after rounds 1 to 20?",
  tot, [57, 60, 66, 70],
  "k = 1,2 give 0; k = 3,4,5 give 1; … k = 18,19,20 give 6. Sum = 3(1+2+3+4+5) + 3·6 − 0 = 45 + 18 = 63. "
  "(70 would be the sum of k/3 without rounding down.)", "content/math/functions-floor-ceiling.svg")

# ---------------------------------------------------------------- modular
S = "math.number-theory.modular"
q(S, 1, "A pool clock reads 9 o'clock. What does the (12-hour) clock read 50 hours later?",
  (9 + 50) % 12, [7, 9, 10, 12],
  "50 = 4·12 + 2, so only the 2 extra hours matter: 9 + 2 = 11 (equivalently 59 ≡ 11 mod 12).",
  "content/math/modular-round-clock.svg")

q(S, 1, "Five agents act as the spotter in a repeating cycle: agent 1 on round 1, agent 2 on round 2, …, agent 5 on round 5, "
        "then agent 1 again on round 6. Which agent is the spotter on round 2027?",
  (2027 - 1) % 5 + 1, [1, 3, 4, 5],
  "Shift to start at 0: (2027 − 1) mod 5 = 2026 mod 5 = 1, so it is the 2nd agent in the cycle (2027 ≡ 2 mod 5).")

nd = sum(1 for k in range(1, 361) if 360 % k == 0)
q(S, 1, "How many positive divisors does 360 have?",
  nd, [12, 18, 20, 30],
  "360 = 2³ · 3² · 5, so the number of divisors is (3 + 1)(2 + 1)(1 + 1) = 24.", "content/math/modular-prime-tree.svg")

q(S, 2, "What is the last digit of 3²⁰²⁷?",
  pow(3, 2027, 10), [1, 2, 3, 9],
  "Last digits of powers of 3 repeat with period 4: 3, 9, 7, 1. Since 2027 ≡ 3 (mod 4), the last digit is the 3rd in the cycle, 7.")

n_ = [n for n in range(11, 40) if n % 4 == 3 and n % 5 == 2]
assert n_ == [27]
q(S, 2, "Cookies are packed 4 per box with 3 left over, and also 5 per box with 2 left over. If there are between 10 and 40 cookies, how many are there?",
  n_[0], [17, 23, 32, 37],
  "n ≡ 3 (mod 4) gives 11, 15, 19, 23, 27, … and n ≡ 2 (mod 5) gives 12, 17, 22, 27, … The only common value is 27 (the next would be 47).")

x_ = [x for x in range(1, 13) if (5 * x) % 13 == 1][0]
q(S, 2, "What is the smallest positive integer x with 5x ≡ 1 (mod 13)?",
  x_, [2, 5, 10, 12],
  "Test 5, 10, 15, 20, 25, 30, 35, 40, …: 40 = 3·13 + 1, so x = 8. (8 is the multiplicative inverse of 5 mod 13.)")

tz = len(str(factorial(50))) - len(str(factorial(50)).rstrip("0"))
q(S, 3, "With how many zeros does 50! end?",
  tz, [10, 11, 13, 50],
  "Each zero comes from a factor 10 = 2·5, and there are plenty of 2s. Count the 5s: ⌊50/5⌋ + ⌊50/25⌋ = 10 + 2 = 12.")

q(S, 3, "What are the last two digits of 7²⁰²⁶?",
  f"{pow(7, 2026, 100):02d}", ["01", "07", "43", "69"],
  "7¹ = 07, 7² = 49, 7³ = 343 → 43, 7⁴ = 2401 → 01, so the last two digits repeat every 4 powers. "
  "2026 ≡ 2 (mod 4), so the answer is 49.")

# ---------------------------------------------------------------- number theory extras
S = "math.number-theory.misc"
q(S, 1, "A custom Valorant game displays its timer code as the binary number 1011001. What is that in ordinary (decimal) numbers?",
  int("1011001", 2), [77, 81, 91, 101],
  "Place values 64, 32, 16, 8, 4, 2, 1: 64 + 16 + 8 + 1 = 89.", "content/math/misc-bases.svg")

q(S, 1, "A rectangular baking tray measures 30 cm by 40 cm. How long is its diagonal?",
  f"{round(math.hypot(30, 40))} cm", ["35 cm", "45 cm", "60 cm", "70 cm"],
  "30-40-50 is a 3-4-5 triple scaled by 10, so the diagonal is 50 cm.", "content/math/misc-triples.svg")

leg = math.isqrt(25**2 - 7**2)
assert leg * leg == 25**2 - 49
q(S, 1, "A right triangle has hypotenuse 25 and one leg 7. What is the other leg?",
  leg, [18, 20, 32, "√674"],
  "7-24-25 is a Pythagorean triple: 7² + 24² = 49 + 576 = 625 = 25².", "content/math/misc-triples.svg")


def to_base(n, b):
    ds = []
    while n:
        ds.append(str(n % b))
        n //= b
    return "".join(reversed(ds)) or "0"


q(S, 2, "Write 345 in base 7.",
  to_base(345, 7), ["1020", "1111", "1200", "2001"],
  "7³ = 343 fits once, leaving 2: 345 = 1·343 + 0·49 + 0·7 + 2, so 1002 in base 7.")

nsol = sum(1 for x in range(1, 100) for y in range(1, 100) if 7 * x + 4 * y == 100)
q(S, 2, "A swim coach builds a 100-lap plan from warm-up sets of 7 laps and sprint sets of 4 laps, using at least one of each. "
        "How many different (warm-up sets, sprint sets) plans are there?",
  nsol, [2, 4, 5, 6],
  "7x + 4y = 100 needs 7x ≡ 0 (mod 4), so x is a multiple of 4: x = 4, 8, 12 give y = 18, 11, 4. That is 3 plans.")

b_ = math.isqrt(41**2 - 9**2)
assert b_ * b_ == 41**2 - 81
q(S, 2, "A right triangle has hypotenuse 41 and a leg of 9. What is its area?",
  9 * b_ // 2, [90, 184.5, 360, 369],
  "9-40-41 is a Pythagorean triple (81 + 1600 = 1681). Area = ½ · 9 · 40 = 180.", "content/math/misc-triples.svg")

npair = sum(1 for x in range(7, 400) for y in range(7, 400) if 6 * (x + y) == x * y)
q(S, 3, "How many ordered pairs (x, y) of positive integers satisfy 1/x + 1/y = 1/6?",
  npair, [6, 8, 12, 18],
  "Clear fractions: xy = 6x + 6y, so (x − 6)(y − 6) = 36. 36 has 9 positive divisors (1, 2, 3, 4, 6, 9, 12, 18, 36), "
  "each giving one pair.")

cnt = 0
for n in range(1, 1001):
    if set(to_base(n, 3)) <= {"0", "1"}:
        cnt += 1
CNT_BASE3 = cnt
q(S, 3, "How many positive integers up to 1000 have only the digits 0 and 1 when written in base 3?",
  cnt, [95, 115, 127, 22], "PLACEHOLDER", "content/math/misc-bases.svg")

# ---------------------------------------------------------------- triangles
S = "math.geometry.triangles"


def heron(a, b, c):
    s = (a + b + c) / 2
    return math.sqrt(s * (s - a) * (s - b) * (s - c))


# independent check by coordinates: A=(0,0), B=(14,0), C chosen so AC=15, BC=13
cx_ = (15**2 - 13**2 + 14**2) / (2 * 14)
cy_ = math.sqrt(15**2 - cx_**2)
area_coord = 14 * cy_ / 2
q(S, 1, "A triangle has sides 13, 14 and 15. What is its area?",
  round(area_coord), [42, 91, 105, 168],
  "Heron: s = 21, area = √(21·8·7·6) = √7056 = 84. (It is a 5-12-13 and a 9-12-15 triangle glued side by side.)",
  "content/math/triangles-special.svg")

ar = 0.5 * 8 * 10 * math.sin(math.radians(30))
q(S, 1, "A triangular pizza slice has two straight edges of 8 cm and 10 cm meeting at a 30° angle. What is its area?",
  f"{round(ar)} cm²", ["10 cm²", "34.6 cm²", "40 cm²", "80 cm²"],
  "Area = ½ab sin C = ½ · 8 · 10 · ½ = 20 cm². Forgetting the ½ gives 40; using sin 60° gives 34.6.",
  "content/math/triangles-special.svg")

q(S, 1, "The centroid of a triangle lies on a median that is 18 cm long. How far is the centroid from the vertex at the end of that median?",
  f"{18 * 2 // 3} cm", ["6 cm", "9 cm", "13.5 cm", "15 cm"],
  "The centroid splits every median 2 : 1 counting from the vertex, so it is 2/3 · 18 = 12 cm from the vertex (and 6 cm from the midpoint of the side).",
  "content/math/triangles-centers.svg")

Hs = heron(13, 14, 15)
q(S, 2, "What is the inradius of the triangle with sides 13, 14 and 15?",
  round(Hs / 21), [3, 5, 6, 8.125],
  "Area = r · s, where s = 21 is the semi-perimeter. r = 84/21 = 4. (8.125 is the circumradius R = abc/(4K), a different circle.)",
  "content/math/triangles-special.svg")

Ax = (0, 0); Bx = (12, 0); Cx = (6, 9)
G_ = (F(Ax[0] + Bx[0] + Cx[0], 3), F(Ax[1] + Bx[1] + Cx[1], 3))
q(S, 2, "Three teammates stand at (0, 0), (12, 0) and (6, 9) on a Valorant map grid. Where is the centroid of their triangle?",
  pt(*G_), ["(6, 0)", "(6, 4.5)", "(6, 9)", "(9, 3)"],
  "The centroid is the average of the vertices: x = (0 + 12 + 6)/3 = 6 and y = (0 + 0 + 9)/3 = 3.")

Aa, Bb = 50, 60
Cc = 180 - Aa - Bb
bic = 180 - (Bb / 2 + Cc / 2)
q(S, 2, "In triangle ABC, ∠A = 50°, ∠B = 60° and ∠C = 70°. The angle bisectors meet at the incenter I. What is ∠BIC?",
  f"{round(bic)}°", ["100°", "110°", "125°", "130°"],
  "In triangle BIC, ∠IBC = 30° and ∠ICB = 35°, so ∠BIC = 180° − 65° = 115° (formula: 90° + A/2).",
  "content/math/triangles-centers.svg")

# coordinates: right angle at A=(0,0), B=(6,0), C=(0,8); incenter = weighted average by opposite side lengths
Ap, Bp, Cp = (0, 0), (6, 0), (0, 8)
la, lb, lc = math.dist(Bp, Cp), math.dist(Ap, Cp), math.dist(Ap, Bp)
I_ = ((la * Ap[0] + lb * Bp[0] + lc * Cp[0]) / (la + lb + lc), (la * Ap[1] + lb * Bp[1] + lc * Cp[1]) / (la + lb + lc))
O_ = ((Bp[0] + Cp[0]) / 2, (Bp[1] + Cp[1]) / 2)
oi2 = (I_[0] - O_[0]) ** 2 + (I_[1] - O_[1]) ** 2
assert abs(oi2 - 5) < 1e-9
q(S, 3, "In the 6-8-10 right triangle, how far apart are the circumcenter and the incenter?",
  "√5", ["√2", "2", "3", "√13"],
  "Put the right angle at the origin with the legs along the axes. The circumcenter is the midpoint of the hypotenuse, (3, 4). "
  "The inradius is (6 + 8 − 10)/2 = 2, so the incenter is (2, 2). Distance = √(1² + 2²) = √5.",
  "content/math/triangles-centers.svg")

q(S, 3, "A triangular pool-toy sail has area 30 cm² and an inscribed circle of radius 2 cm. What is the perimeter of the sail?",
  f"{2 * (30 // 2)} cm", ["15 cm", "32 cm", "45 cm", "60 cm"],
  "Area = r · s with s the semi-perimeter: 30 = 2s, so s = 15. The perimeter is 2s = 30 cm.",
  "content/math/triangles-special.svg")

# ---------------------------------------------------------------- circles
S = "math.geometry.circles"
q(S, 1, "An inscribed angle intercepts an arc of 100°. How big is the inscribed angle?",
  "50°", ["25°", "100°", "130°", "200°"],
  "An inscribed angle is half of the arc (central angle) it intercepts: 100°/2 = 50°.", "content/math/circles-angles.svg")

q(S, 1, "ABCD is a cyclic quadrilateral with ∠A = 70°. What is ∠C?",
  f"{180 - 70}°", ["20°", "70°", "90°", "290°"],
  "Opposite angles of a cyclic quadrilateral add up to 180°: ∠C = 180° − 70° = 110°.", "content/math/circles-angles.svg")

dd = math.sqrt(10**2 - 6**2)
q(S, 1, "A swimmer treads water at a point on the edge of a circular pool, 6 m from one end of a 10 m diameter. "
        "How far is she from the other end of that diameter?",
  f"{round(dd)} m", ["4 m", "7 m", "16 m", "√136 m"],
  "An angle inscribed in a semicircle is 90°, so the triangle is right-angled with hypotenuse 10: √(10² − 6²) = 8 m.",
  "content/math/circles-angles.svg")

pd_ = F(4 * 9, 6)
q(S, 2, "Two chords AB and CD of a circle cross at P. PA = 4, PB = 9 and PC = 6. What is PD?",
  fr(pd_), [7.5, 13, 24, 36],
  "Power of a point: PA · PB = PC · PD, so 4·9 = 6·PD and PD = 6.", "content/math/circles-power.svg")

r1, r2 = 4, 25
tl = math.sqrt((r1 + r2) ** 2 - (r2 - r1) ** 2)
q(S, 2, "Two round pans with radii 4 cm and 25 cm touch each other on a table. How long is their common outer tangent line segment between the two touching points on the pans?",
  f"{round(tl)} cm", ["10 cm", "21 cm", "29 cm", "40 cm"],
  "The centers are 4 + 25 = 29 apart. The tangent length is √(29² − (25 − 4)²) = √(841 − 441) = 20 cm (or 2√(4·25) = 20).",
  "content/math/circles-tangent.svg")

tg = math.sqrt(17**2 - 8**2)
q(S, 2, "In a made-up Valorant map, a smoke covers a circle of radius 8 m. You stand 17 m from its center. "
        "How long is your straight line of sight that just touches the edge of the smoke (the tangent length)?",
  f"{round(tg)} m", ["9 m", "12 m", "17 m", "25 m"],
  "The tangent is perpendicular to the radius, giving a right triangle with hypotenuse 17 and a leg 8: √(17² − 8²) = 15 m.",
  "content/math/circles-tangent.svg")

PB = 144 / 8
q(S, 3, "From an outside point P, a tangent PT of length 12 touches a circle, and a secant from P meets the circle at A (nearer) and B (farther) with PA = 8. What is the length of chord AB?",
  f"{round(PB - 8)}", [4.5, 6, 14, 18],
  "Tangent-secant: PT² = PA · PB, so 144 = 8 · PB and PB = 18. The chord is AB = PB − PA = 18 − 8 = 10.",
  "content/math/circles-power.svg")

arc_bc, arc_cd = 2 * 40, 2 * 30
arc_bd = arc_bc + arc_cd
bcd = (360 - arc_bd) / 2
q(S, 3, "ABCD is a cyclic quadrilateral with ∠BAC = 40° and ∠CBD = 30°. What is ∠BCD?",
  f"{round(bcd)}°", ["70°", "100°", "120°", "140°"],
  "∠BAC = 40° means arc BC = 80°, and ∠CBD = 30° means arc CD = 60°. The arc from B through C to D is 140°, so ∠BAD = 70°. The other arc BD (through A) is 360° − 140° = 220°, so ∠BCD = 220°/2 = 110°. Check: 70° + 110° = 180°.",
  "content/math/circles-angles.svg")

# ---------------------------------------------------------------- transformations
S = "math.geometry.transformations"
rot90 = lambda p, c=(0, 0): (c[0] - (p[1] - c[1]), c[1] + (p[0] - c[0]))
q(S, 1, "The point (3, −2) is rotated 90° counterclockwise about the origin. Where does it land?",
  pt(*rot90((3, -2))), ["(−2, −3)", "(−2, 3)", "(−3, 2)", "(3, 2)"],
  "A 90° counterclockwise rotation sends (x, y) to (−y, x): (3, −2) → (2, 3).", "content/math/transformations-four.svg")

q(S, 1, "The point (−3, 8) is reflected in the line y = x. Where does it land?",
  pt(8, -3), ["(−8, 3)", "(−3, −8)", "(3, −8)", "(3, 8)"],
  "Reflecting in y = x swaps the coordinates: (−3, 8) → (8, −3).", "content/math/transformations-four.svg")

q(S, 1, "The point (2, 5) is translated by the vector (−4, 3). Where does it land?",
  pt(2 - 4, 5 + 3), ["(−6, 8)", "(−2, 2)", "(2, 8)", "(6, 2)"],
  "Add the vector: (2 − 4, 5 + 3) = (−2, 8).", "content/math/transformations-four.svg")

q(S, 2, "A cookie cutter makes cookies of area 12 cm². A bigger cutter is a dilation of it by scale factor 2.5. What is the area of a cookie from the bigger cutter?",
  f"{12 * 2.5 ** 2:g} cm²", ["30 cm²", "36 cm²", "60 cm²", "150 cm²"],
  "Lengths scale by 2.5, areas scale by 2.5² = 6.25: 12 · 6.25 = 75 cm².", "content/math/transformations-four.svg")

p = (4, 2)
p = (-p[0], p[1])
p = (p[0] + 3, p[1] + 1)
q(S, 2, "The point (4, 2) is reflected in the y-axis and then translated by (3, 1). Where does it end up?",
  pt(*p), ["(−7, 3)", "(−1, 1)", "(1, 3)", "(7, 3)"],
  "Reflect in the y-axis: (4, 2) → (−4, 2). Translate: (−4 + 3, 2 + 1) = (−1, 3).", "content/math/transformations-four.svg")

c_ = (1, 1)
pr = (2 * c_[0] - 4, 2 * c_[1] - 3)
assert pr == rot90(rot90((4, 3), c_), c_)
q(S, 2, "The point (4, 3) is rotated 180° about the point (1, 1). Where does it land?",
  pt(*pr), ["(−4, −3)", "(−3, −2)", "(−2, 1)", "(2, 1)"],
  "A 180° rotation about C sends P to 2C − P: (2 − 4, 2 − 3) = (−2, −1). C is the midpoint of P and its image.")

# reflect (5,1) in y = x + 1 : projection onto the line
P0 = (5, 1)
d_ = (1, 1)
pnt = (0, 1)
tproj = F((P0[0] - pnt[0]) * d_[0] + (P0[1] - pnt[1]) * d_[1], 2)
foot = (pnt[0] + tproj * d_[0], pnt[1] + tproj * d_[1])
img = (2 * foot[0] - P0[0], 2 * foot[1] - P0[1])
q(S, 3, "In a made-up Valorant map, a mirror-like wall lies along the line y = x + 1. What is the reflection of the point (5, 1) in this wall?",
  pt(*img), ["(−1, 6)", "(0, 4)", "(1, 5)", "(6, 0)"],
  "Shift the line down by 1 so it becomes y = x, reflect (swap), shift back: (5, 1) → (5, 0) → (0, 5) → (0, 6). "
  "The midpoint (2.5, 3.5) is on the line, so the answer checks out.", "content/math/transformations-four.svg")

pp = (0, 2)
pp = (2 * 1 - pp[0], pp[1])
pp = (2 * 4 - pp[0], pp[1])
q(S, 3, "In a pool, a ball at (0, 2) is reflected in the wall line x = 1 and then the image is reflected in the wall line x = 4. Where does it end up?",
  pt(*pp), ["(−6, 2)", "(3, 2)", "(4, 2)", "(8, 2)"],
  "Reflect in x = 1: (0, 2) → (2, 2). Reflect in x = 4: (2, 2) → (6, 2). Two reflections in parallel lines make a translation by twice the distance between them (2 · 3 = 6).",
  "content/math/transformations-four.svg")

# ---------------------------------------------------------------- coordinate
S = "math.geometry.coordinate"
q(S, 1, "On a Valorant map grid (1 unit = 1 m), a camera sits at (1, 2) and a site marker at (7, 10). How far apart are they?",
  f"{round(math.dist((1, 2), (7, 10)))} m", ["6 m", "8 m", "14 m", "√28 m"],
  "Distance = √((7 − 1)² + (10 − 2)²) = √(36 + 64) = 10 m (a 6-8-10 triangle).", "content/math/coordinate-lines.svg")

on = [p for p in [(7, 2), (7, 3), (-1, 1), (5, 2), (3, 5)] if (p[0] - 3) ** 2 + (p[1] + 1) ** 2 == 25]
assert on == [(7, 2)]
q(S, 1, "Which of these points lies on the circle (x − 3)² + (y + 1)² = 25?",
  "(7, 2)", ["(7, 3)", "(−1, 1)", "(5, 2)", "(3, 5)"],
  "Substitute: (7 − 3)² + (2 + 1)² = 16 + 9 = 25. ✓. The others give 32, 20, 13 and 36.", "content/math/coordinate-circle-shoelace.svg")

m_ = F(11 - 3, 4 - 0)
c0 = 3
q(S, 1, "Which line passes through (0, 3) and (4, 11)?",
  f"y = {fr(m_)}x + {c0}", ["y = 2x − 3", "y = 3x + 2", "y = x/2 + 3", "y = 8x + 3"],
  "Slope = (11 − 3)/(4 − 0) = 2, and the y-intercept is the y-value at x = 0, which is 3. So y = 2x + 3.",
  "content/math/coordinate-lines.svg")

sol = [(x, 2 * x + 1) for x in range(-20, 21) if 3 * x + 2 * (2 * x + 1) == 16]
q(S, 2, "Where do the lines y = 2x + 1 and 3x + 2y = 16 cross?",
  pt(*sol[0]), ["(2, 3)", "(3, 7)", "(4, 9)", "(5, 2)"],
  "Substitute y = 2x + 1: 3x + 4x + 2 = 16, so x = 2 and y = 5.", "content/math/coordinate-lines.svg")

# line through (4, 1) perpendicular to y = 2x + 5
mperp = F(-1, 2)
cc = 1 - mperp * 4
q(S, 2, "A line passes through (4, 1) and is perpendicular to y = 2x + 5. Where does it cross the y-axis?",
  f"(0, {fr(cc)})", ["(0, −1)", "(0, 1)", "(0, 5)", "(0, 7)"],
  "Perpendicular slopes multiply to −1, so m = −½. Then y − 1 = −½(x − 4), i.e. y = −½x + 3: it crosses the y-axis at (0, 3).")

# x² + y² − 6x + 8y = 0  ->  (x−3)² + (y+4)² = 25
h_, k_ = 3, -4
r2_ = 0 - 0 + h_**2 + k_**2
q(S, 2, "The edge of a round paddling pool drawn on a plan is x² + y² − 6x + 8y = 0 (units: m). What is its radius?",
  f"{math.isqrt(r2_)} m", ["3 m", "4 m", "10 m", "25 m"],
  "Complete the squares: (x − 3)² + (y + 4)² = 9 + 16 = 25, so the radius is √25 = 5 m (25 is r², not r).",
  "content/math/coordinate-circle-shoelace.svg")


def shoelace(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2


q(S, 3, "A baking tray has its four corners at (0, 0), (6, 0), (8, 5) and (2, 7) (units: cm). What is its area?",
  f"{shoelace([(0, 0), (6, 0), (8, 5), (2, 7)]):g} cm²", ["19 cm²", "36 cm²", "42 cm²", "76 cm²"],
  "Shoelace: terms 0·0 − 6·0 = 0; 6·5 − 8·0 = 30; 8·7 − 2·5 = 46; 2·0 − 0·7 = 0. Sum = 76, area = ½ · 76 = 38 cm². "
  "(76 forgets the ½.)", "content/math/coordinate-circle-shoelace.svg")

# y = x and y = 8 - x meet at (4,4); with the x-axis: (0,0), (8,0)
meet = [(x, x) for x in range(0, 9) if x == 8 - x][0]
q(S, 3, "The lines y = x and y = 8 − x and the x-axis form a triangle. What is its area?",
  f"{shoelace([(0, 0), (8, 0), meet]):g}", [8, 12, 24, 32],
  "The vertices are (0, 0) [y = x meets the axis], (8, 0) [y = 8 − x meets the axis] and (4, 4) [the two lines meet]. "
  "Base 8, height 4: area = ½·8·4 = 16 (shoelace agrees).", "content/math/coordinate-lines.svg")

# ---------------------------------------------------------------- solid geometry
S = "math.geometry.solid"
q(S, 1, "A cylinder has radius 3 and height 10. What is its volume?",
  f"{3 * 3 * 10}π", ["30π", "60π", "180π", "900π"],
  "V = πr²h = π · 9 · 10 = 90π.", "content/math/solid-formulas.svg")

q(S, 1, "A cylindrical soup pot has radius 10 cm and height 15 cm. What is its volume?",
  f"{10 * 10 * 15}π cm³", ["500π cm³", "750π cm³", "3000π cm³", "4500π cm³"],
  "V = πr²h = π · 100 · 15 = 1500π cm³ (about 4.7 liters).", "content/math/solid-formulas.svg")

q(S, 1, "A square pyramid has a base of side 6 and a height of 4. What is its volume?",
  F(1, 3) * 36 * 4, [24, 72, 96, 144],
  "V = ⅓ · base area · height = ⅓ · 36 · 4 = 48. (144 forgets the ⅓.)", "content/math/solid-formulas.svg")

sl = math.hypot(6, 8)
q(S, 2, "A cone has radius 6 and height 8. What is its total surface area (base included)?",
  f"{round(36 + 6 * sl)}π", ["36π", "60π", "120π", "132π"],
  "Slant height ℓ = √(6² + 8²) = 10. Base π·36 plus side π·r·ℓ = π·60: total 96π.", "content/math/solid-nets.svg")

area = 25 * 10 + 2 * (25 * 2) + 2 * (10 * 2)
q(S, 2, "A rectangular pool is 25 m long, 10 m wide and 2 m deep. How many m² of tile are needed for the floor and the four walls (no tile on top)?",
  area, [140, 350, 500, 640],
  "Floor 25·10 = 250; two long walls 2·(25·2) = 100; two short walls 2·(10·2) = 40. Total 390 m². "
  "(500 is the volume in m³.)", "content/math/solid-formulas.svg")

q(S, 2, "In a made-up Valorant map, a smoke ball is a sphere of radius 3 m with volume 36π m³. If an upgrade doubles the radius to 6 m, what is the new volume?",
  f"{round(F(4, 3) * 216)}π m³", ["72π m³", "144π m³", "216π m³", "576π m³"],
  "Volume scales with the cube of the length: doubling the radius multiplies the volume by 2³ = 8, so 8 · 36π = 288π. "
  "Check: 4/3 · π · 6³ = 288π.", "content/math/solid-formulas.svg")

Vc = F(1, 3) * 3 * 3 * 12  # in units of pi
R3 = round((Vc * 3 / 4) ** (1 / 3))
assert F(4, 3) * R3**3 == Vc
q(S, 3, "A cone-shaped piece of fondant with radius 3 cm and height 12 cm is rolled into a perfect ball with no loss. What is the radius of the ball?",
  f"{R3} cm", ["2 cm", "4 cm", "6 cm", "9 cm"],
  "Cone volume = ⅓π·9·12 = 36π. Ball: 4/3·πR³ = 36π, so R³ = 27 and R = 3 cm.", "content/math/solid-formulas.svg")

r_ = 3
Vs = F(4, 3) * r_**3
Vcyl = r_**2 * 2 * r_
q(S, 3, "A tennis ball (a sphere of radius 3 cm) fits snugly in a tube of the same radius and height 6 cm. What fraction of the tube is empty?",
  fr(1 - Vs / Vcyl), ["1/6", "1/4", "1/2", "2/3"],
  "Ball: 4/3·π·27 = 36π. Tube: π·9·6 = 54π. Ball fills 36/54 = 2/3, so 1/3 of the tube is empty.", "content/math/solid-formulas.svg")

# ---------------------------------------------------------------- counting principles
S = "math.combinatorics.counting-principles"
q(S, 1, "A sandwich needs 1 of 4 breads, 1 of 3 fillings and 1 of 2 sauces. How many different sandwiches are possible?",
  4 * 3 * 2, [9, 12, 14, 32],
  "Independent choices one after another multiply: 4 · 3 · 2 = 24.", "content/math/counting-product-grid.svg")

q(S, 1, "For today's set you choose either one of 6 freestyle drills or one of 4 backstroke drills (not both). How many choices do you have?",
  6 + 4, [2, 20, 24, 48],
  "Alternatives that cannot happen together add: 6 + 4 = 10. (24 would be the product, for doing both.)",
  "content/math/counting-product-grid.svg")

both = 25 + 18 - (40 - 5)
q(S, 1, "In a class of 40, 25 like cooking, 18 like swimming and 5 like neither. How many like both?",
  both, [3, 5, 13, 43],
  "|C ∪ S| = 40 − 5 = 35 and |C ∪ S| = 25 + 18 − |C ∩ S|, so |C ∩ S| = 43 − 35 = 8.", "content/math/counting-inclusion-exclusion.svg")

q(S, 2, "In a lobby of 50 players, each picks one of 7 agents. At least how many players are guaranteed to have picked the same agent?",
  -(-50 // 7), [6, 7, 9, 43],
  "Pigeonhole: 50 players into 7 boxes. If every agent had at most 7 players, there would be at most 49. "
  "So some agent has ⌈50/7⌉ = 8.", "content/math/counting-pigeonhole-coloring.svg")

nums = list(range(1, 21))
while len(nums) > 1:
    random.Random(len(nums)).shuffle(nums)
    a_, b_ = nums.pop(), nums.pop()
    nums.append(a_ + b_ - 1)
q(S, 2, "The numbers 1, 2, 3, …, 20 are on a board. A move erases two numbers a and b and writes a + b − 1. After 19 moves one number is left. What is it?",
  nums[0], [190, 200, 209, 210],
  "Each move lowers the total by exactly 1 (a + b becomes a + b − 1). The total starts at 210, and after 19 moves it is 210 − 19 = 191, whatever order you pick.")

best = max(m for m in range(5, 41) if any(sum(c) == 40 - m for c in itertools.combinations(range(1, m), 4)))
assert best == 30
q(S, 2, "Five different positive whole numbers add up to 40. What is the largest value the biggest of them can have?",
  best, [25, 29, 31, 36],
  "To make one number as big as possible, make the other four as small as possible: 1 + 2 + 3 + 4 = 10, so the biggest is 40 − 10 = 30.")

# 8x8 board, remove (0,0) and (7,7); a domino covers one square of each colour
colors = [(r, c) for r in range(8) for c in range(8) if (r, c) not in {(0, 0), (7, 7)}]
w_ = sum(1 for r, c in colors if (r + c) % 2 == 0)
k_ = sum(1 for r, c in colors if (r + c) % 2 == 1)
q(S, 3, "Two opposite corners are cut off an 8 × 8 chessboard. What is the greatest number of dominoes (each covering 2 neighboring squares) that can be placed without overlapping?",
  min(w_, k_), [28, 29, 31, 32],
  "Opposite corners have the same color, so the board has 30 squares of one color and 32 of the other. Each domino covers one of each, "
  "so at most 30 dominoes fit (and 30 can be placed).", "content/math/counting-pigeonhole-coloring.svg")

c235 = sum(1 for n in range(1, 101) if n % 2 == 0 or n % 3 == 0 or n % 5 == 0)
q(S, 3, "How many integers from 1 to 100 are divisible by 2, by 3 or by 5 (at least one of them)?",
  c235, [70, 73, 78, 84],
  "50 + 33 + 20 − (16 + 10 + 6) + 3 = 103 − 32 + 3 = 74 (inclusion-exclusion).", "content/math/counting-inclusion-exclusion.svg")

# ---------------------------------------------------------------- enumerative
S = "math.combinatorics.enumerative"
q(S, 1, "From 8 toppings you pick 3 for a pizza (order does not matter). How many different pizzas can you make?",
  comb(8, 3), [24, 28, 336, 512],
  "Combinations: C(8,3) = 8·7·6/(3·2·1) = 56. (336 counts the picks in order.)", "content/math/enumerative-team-pick.svg")

q(S, 1, "Five swimmers are put in 5 different lanes. In how many ways can that be done?",
  len(list(itertools.permutations(range(5)))), [24, 25, 60, 3125],
  "Permutations: 5! = 5·4·3·2·1 = 120.", "content/math/enumerative-team-pick.svg")

q(S, 1, "Rows of Pascal's triangle start at row 0 (which is just 1). What is the middle number of row 6?",
  comb(6, 3), [10, 15, 30, 36],
  "Row 6 is 1, 6, 15, 20, 15, 6, 1. The middle number is C(6,3) = 20 (= 10 + 10 from the row above).", "content/math/pascal-triangle.svg")

q(S, 2, "In how many ways can 10 identical lemons be put into 4 bowls if a bowl may stay empty?",
  comb(13, 3), [40, 84, 210, 715],
  "Stars and bars: 10 stars and 3 dividers, C(13,3) = 286. (84 = C(9,3) would force at least one lemon per bowl.)",
  "content/math/enumerative-stars-and-bars.svg")

q(S, 2, "A Valorant team of 5 is picked from 12 agents, and one specific agent must be on it. How many different teams are possible?",
  comb(11, 4), [220, 462, 495, 792],
  "The special agent is in, so choose the other 4 from the remaining 11: C(11,4) = 330. (792 = C(12,5) ignores the rule.)",
  "content/math/enumerative-team-pick.svg")

arr = len(set(itertools.permutations("BUTTER")))
q(S, 2, "How many different arrangements of the letters of the word BUTTER are there?",
  arr, [60, 120, 180, 720],
  "6 letters with T repeated twice: 6!/2! = 720/2 = 360.")


def count_partitions(n, maxpart=None):
    maxpart = maxpart or n
    if n == 0:
        return 1
    return sum(count_partitions(n - k, k) for k in range(1, min(n, maxpart) + 1))


q(S, 3, "In how many ways can 7 be written as a sum of positive integers when the order does not matter? (For example 4 + 2 + 1 and 2 + 4 + 1 count as the same.)",
  count_partitions(7), [13, 14, 16, 21],
  "List by largest part: 7; 6+1; 5+2, 5+1+1; 4+3, 4+2+1, 4+1+1+1; 3+3+1, 3+2+2, 3+2+1+1, 3+1+1+1+1; 2+2+2+1, 2+2+1+1+1, 2+1+1+1+1+1; 1×7. That is 15.",
  "content/math/enumerative-partitions.svg")

inc = sum(1 for n in range(100, 1000) if str(n)[0] < str(n)[1] < str(n)[2])
q(S, 3, "How many 3-digit numbers have strictly increasing digits (like 359 or 128)?",
  inc, [72, 90, 120, 126],
  "A 3-digit number with increasing digits is determined by choosing 3 different digits, and they must be nonzero (0 would have to be first). "
  "So C(9,3) = 84. (C(10,3) = 120 wrongly allows a 0.)", "content/math/pascal-triangle.svg")

# ---------------------------------------------------------------- probability
S = "math.combinatorics.probability"
q(S, 1, "Two fair dice are rolled. What is the probability that the sum is 8?",
  fr(F(sum(1 for a in range(1, 7) for b in range(1, 7) if a + b == 8), 36)), ["1/6", "1/9", "1/8", "7/36"],
  "The pairs (2,6), (3,5), (4,4), (5,3), (6,2) make 8: 5 out of 36 equally likely outcomes.", "content/math/probability-sample-space.svg")

q(S, 1, "In a made-up Valorant scrim, your team wins each round with probability 0.6, independently. What is the probability of winning two rounds in a row?",
  "0.36", ["0.12", "0.48", "0.6", "0.84"],
  "Independent events multiply: 0.6 × 0.6 = 0.36. (0.84 would be the chance of winning at least one of the two.)",
  "content/math/probability-tree.svg")

q(S, 1, "A bag has 5 red and 3 green peppers. You pick one without looking. What is the probability it is red?",
  fr(F(5, 8)), ["1/8", "3/8", "1/2", "5/7"],
  "5 red out of 8 peppers in total: 5/8.")

q(S, 2, "A fair die is rolled 3 times. What is the probability of at least one six?",
  fr(1 - F(5, 6) ** 3), ["1/6", "1/2", "25/36", "125/216"],
  "Complement: P(no six in 3 rolls) = (5/6)³ = 125/216, so P(at least one) = 1 − 125/216 = 91/216.",
  "content/math/probability-tree.svg")

q(S, 2, "Of 30 swimmers, 18 can swim butterfly, 20 can swim backstroke and 12 can do both. A swimmer who can do butterfly is chosen at random. What is the probability that she can also do backstroke?",
  fr(F(12, 18)), ["2/5", "1/2", "1/3", "3/5"],
  "Conditional probability: only the 18 butterfly swimmers count, and 12 of them also do backstroke: 12/18 = 2/3. "
  "(3/5 = 12/20 would be P(butterfly | backstroke), the other way round.)", "content/math/probability-two-way-table.svg")

q(S, 2, "Two cards are drawn from a standard deck of 52 cards without replacement. What is the probability that both are aces?",
  fr(F(4, 52) * F(3, 51)), ["1/169", "1/52", "4/221", "1/13"],
  "P(first ace) = 4/52, then P(second ace | first ace) = 3/51. Product: 12/2652 = 1/221.",
  "content/math/probability-tree.svg")

pA, dA, dB = F(2, 5), F(9, 10), F(1, 5)
post = pA * dA / (pA * dA + (1 - pA) * dB)
q(S, 3, "In a made-up Valorant scenario the spike is on site A with probability 0.4 and on site B otherwise. A camera spots something "
        "with probability 0.9 if the spike is on A, and 0.2 if it is on B. The camera spots something. What is the probability the spike is on A?",
  fr(post), ["2/5", "1/2", "3/5", "9/10"],
  "P(spot) = 0.4·0.9 + 0.6·0.2 = 0.36 + 0.12 = 0.48. P(A | spot) = 0.36/0.48 = 3/4. "
  "(The tempting 9/10 is P(spot | A), the other direction.)", "content/math/probability-tree.svg")

out = [(a, b) for a in range(1, 7) for b in range(1, 7) if a == 6 or b == 6]
good = [(a, b) for a, b in out if a + b >= 10]
q(S, 3, "Two fair dice are rolled, and you are told at least one shows a 6. What is the probability that the sum is at least 10?",
  fr(F(len(good), len(out))), ["1/6", "5/36", "6/11", "1/2"],
  "Given at least one six there are 11 equally likely outcomes. Sum ≥ 10 among them: (6,4), (4,6), (6,5), (5,6), (6,6) = 5. So 5/11.",
  "content/math/probability-sample-space.svg")

# ---------------------------------------------------------------- strategies
S = "math.combinatorics.strategies"
tot = sum(1 for n in range(10, 100) if "5" in str(n))
q(S, 1, "How many 2-digit numbers (10 to 99) contain at least one digit 5?",
  tot, [10, 17, 19, 20],
  "Complement: numbers with no 5 have a tens digit from 8 choices (1–9 without 5) and a units digit from 9 choices (0–9 without 5): 72. 90 − 72 = 18.",
  "content/math/strategies-lanes-complement.svg")

q(S, 1, "How many integers x satisfy |x − 2| ≤ 3?",
  sum(1 for x in range(-50, 50) if abs(x - 2) <= 3), [3, 5, 6, 8],
  "Casework on the sign: x − 2 between −3 and 3, so −1 ≤ x ≤ 5. That is −1, 0, 1, 2, 3, 4, 5: seven integers.",
  "content/math/strategies-toolbox.svg")

wins = sum(1 for a in range(1, 7) for b in range(1, 7) if a > b)
q(S, 1, "In a made-up Valorant custom game each team rolls a fair die to decide the pick order. What is the probability that team 1 rolls strictly higher than team 2?",
  fr(F(wins, 36)), ["1/6", "1/3", "1/2", "7/12"],
  "By symmetry P(team 1 higher) = P(team 2 higher). Ties have probability 6/36 = 1/6, so each side gets (1 − 1/6)/2 = 5/12.",
  "content/math/strategies-toolbox.svg")

ev = sum(1 for mask in range(2**8) if bin(mask).count("1") % 2 == 0)
q(S, 2, "A coach picks a relay squad from 8 swimmers. How many squads have an even number of swimmers? (The empty squad counts.)",
  ev, [64, 127, 255, 256],
  "Bijection: for any squad, toggle swimmer #1 (add or remove). This pairs every even squad with a different odd squad, "
  "so exactly half of the 2⁸ = 256 squads are even: 128.", "content/math/strategies-grid-bijection.svg")

rep = sum(1 for n in range(10000) if len(set(f"{n:04d}")) < 4)
q(S, 2, "A pantry lock has a 4-digit code (0000 to 9999). How many codes have at least one repeated digit?",
  rep, [4959, 5000, 5040, 9000],
  "Complement: codes with 4 different digits are 10·9·8·7 = 5040. So 10 000 − 5040 = 4960.",
  "content/math/strategies-lanes-complement.svg")


def combos(n, parts):
    if n == 0:
        return 1
    if not parts:
        return 0
    p0 = parts[0]
    return sum(combos(n - k * p0, parts[1:]) for k in range(n // p0 + 1))


q(S, 2, "In a made-up Valorant shop you spend exactly 500 credits on shields that cost 100, 200 or 500 credits each (you may buy any number of each). "
        "How many different combinations are there? (Order does not matter.)",
  combos(5, [5, 2, 1]), [3, 5, 6, 8],
  "Casework on the number of 500-credit shields and 200-credit shields: 500 alone; 200+200+100; 200+100+100+100; 100×5. That is 4 combinations.", "content/math/strategies-toolbox.svg")

before = sum(1 for p in itertools.permutations("STROKE") if p.index("S") < p.index("T"))
q(S, 3, "In how many arrangements of the letters S, T, R, O, K, E (each used once) does S come before T?",
  before, [120, 180, 240, 720],
  "Symmetry: swapping S and T pairs every arrangement with S first with one with T first. So exactly half of 6! = 720 qualify: 360.",
  "content/math/strategies-toolbox.svg")

ev4 = sum(1 for n in range(1000, 10000) if len(set(str(n))) == 4 and n % 2 == 0)
q(S, 3, "How many 4-digit numbers (1000 to 9999) have four different digits and are even?",
  ev4, [2240, 2304, 2520, 4536],
  "Casework on the last digit. Last digit 0: 9·8·7 = 504. Last digit 2, 4, 6 or 8 (4 choices): the first digit avoids 0 and the last, so 8 choices, "
  "then 8 and 7: 4·8·8·7 = 1792. Total 504 + 1792 = 2296.", "content/math/strategies-toolbox.svg")

# fix the base-3 explanation now that the count is known
for item in QS:
    if item["expl"] == "PLACEHOLDER":
        assert 127 - CNT_BASE3 == 22
        item["expl"] = ("Numbers with only the digits 0 and 1 in base 3 correspond to sums of distinct powers of 3. "
                        "Up to 7 digits (below 3⁷ = 2187) there are 2⁷ − 1 = 127 positive ones. Those that use 3⁶ = 729 and also "
                        "more than 271 from the smaller powers exceed 1000: there are 22 of them. 127 − 22 = 105.")

# ------------------------------------------------------------------ assemble
SUBS = []
for item in QS:
    if item["sub"] not in SUBS:
        SUBS.append(item["sub"])


def build():
    rng = random.Random(22)
    n = len(QS)
    pos = [i % 5 for i in range(n)]
    rng.shuffle(pos)
    out = []
    for i, item in enumerate(QS):
        letters = "ABCDE"
        wrong = list(item["wrong"])
        choices = {}
        p = pos[i]
        it = iter(wrong)
        for j, L in enumerate(letters):
            choices[L] = item["correct"] if j == p else next(it)
        out.append({
            "id": f"math-{i + 1:04d}",
            "subtopic": item["sub"],
            "difficulty": item["d"],
            "stem": item["stem"],
            "visual": item["visual"],
            "choices": choices,
            "answer": letters[p],
            "explanation": item["expl"],
            "explanation_visual": item["ev"],
            "source": "original",
        })
    return {"version": 1, "subject": "math", "questions": out}


if __name__ == "__main__":
    data = build()
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if "--write" in sys.argv:
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT} ({len(data['questions'])} questions)")
    else:
        cur = json.loads(OUT.read_text(encoding="utf-8"))
        bad = 0
        for a, b in zip(cur["questions"], data["questions"]):
            if a["choices"][a["answer"]] != b["choices"][b["answer"]] or a["answer"] != b["answer"]:
                print("MISMATCH", a["id"])
                bad += 1
        if len(cur["questions"]) != len(data["questions"]):
            print("COUNT MISMATCH")
            bad += 1
        if bad:
            sys.exit(1)
    letters = [qq["answer"] for qq in data["questions"]]
    for L in "ABCDE":
        share = letters.count(L) / len(letters)
        assert share <= 0.30, f"letter {L} has {share:.0%}"
    print("answer letters:", {L: letters.count(L) for L in "ABCDE"})
    print(f"OK: {len(data['questions'])} questions recomputed and matched the keys")
