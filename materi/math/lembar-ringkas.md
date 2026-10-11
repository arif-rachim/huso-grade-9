# 🟦 HUSO Maths Cheat Sheet, Grade 9–10

> 🖨️ Print 2 pages (Ctrl+P). The HUSO exam does **not** give you formulas, so learn all of these by heart. Round 1 allows a scientific calculator (not graphing).

---
## 📄 Page 1: Algebra & Number Theory

### 🏊 Polynomials
| Topic | Formula |
|---|---|
| **Remainder & factor** | P(x) divided by (x − a) → remainder **P(a)**. P(a) = 0 ⇔ (x − a) is a factor |
| **Factoring patterns** | a² − b² = (a − b)(a + b) · (a ± b)² = a² ± 2ab + b² · a³ ± b³ = (a ± b)(a² ∓ ab + b²) |
| **Vieta, quadratic** ax² + bx + c | p + q = **−b/a** · pq = **c/a** · p² + q² = (p + q)² − 2pq |
| **Vieta, cubic** ax³ + bx² + cx + d | p + q + r = **−b/a** · pq + qr + rp = **c/a** · pqr = **−d/a** |
| **Rational roots** | root m/n (lowest terms): **m divides the constant term**, **n divides the leading coefficient** |
| **Binomial** | (a + b)ⁿ = Σ C(n, k) aⁿ⁻ᵏ bᵏ · sum of coefficients = **P(1)** · constant term = **P(0)** |

### 🎮 Sequences & series
| Type | nth term | Sum of n terms |
|---|---|---|
| **Arithmetic** (difference d) | aₙ = a₁ + (n − 1)d | Sₙ = n(a₁ + aₙ)/2 |
| **Geometric** (ratio r) | aₙ = a₁ rⁿ⁻¹ | Sₙ = a₁(1 − rⁿ)/(1 − r), r ≠ 1 · infinite (\|r\| < 1): a₁/(1 − r) |
| **Telescoping** | write each term as a difference | 1/(k(k + 1)) = 1/k − 1/(k + 1) → sum of n terms = **n/(n + 1)** |

### 🍳 Inequalities
- **Trivial:** x² ≥ 0 for every real number (equal to 0 only when x = 0).
- **AM-GM** (a, b ≥ 0): (a + b)/2 ≥ √(ab), with equality when **a = b**. For n numbers: the average ≥ the nth root of the product.
- **Order:** HM ≤ GM ≤ AM, that is 2ab/(a + b) ≤ √(ab) ≤ (a + b)/2.
- **Triangle:** |a − b| < c < a + b.

### 🍳 Functions
- **Injective** = each output comes from at most 1 input · **Surjective** = every element of the codomain is hit · **Bijective** = both (has an inverse).
- **Even:** f(−x) = f(x) (symmetric about the y-axis) · **Odd:** f(−x) = −f(x) (symmetric about the origin).
- **Floor ⌊x⌋** = the greatest integer ≤ x · **Ceiling ⌈x⌉** = the smallest integer ≥ x · x − 1 < ⌊x⌋ ≤ x.
- **Log:** log(ab) = log a + log b · log(a/b) = log a − log b · log aᵏ = k log a · log_b b = 1 · log 1 = 0.
- **Trigonometry:** sin²θ + cos²θ = 1 · sin(90° − θ) = cos θ

| θ | 30° | 45° | 60° |
|---|---|---|---|
| sin | ½ | √2/2 | √3/2 |
| cos | √3/2 | √2/2 | ½ |
| tan | 1/√3 | 1 | √3 |

### 🎮 Modular arithmetic & 🍳 number theory
- a ≡ b (mod m) ⇔ **m divides (a − b)**. You may add, subtract, multiply and raise to powers.
- Big powers: look for a **repeating pattern** (cycle) of remainders.
- **Prime factorization** is unique. If n = pᵃ qᵇ, the number of divisors is **(a + 1)(b + 1)**.
- **Pythagorean triples:** 3-4-5 · 5-12-13 · 8-15-17 · 7-24-25 · 20-21-29 · 9-40-41 (and their multiples).
- **Diophantine** ax + by = c has integer solutions ⇔ **gcd(a, b) divides c**.
- **Bases:** 1011₂ = 8 + 2 + 1 = 11. To convert to base b: divide repeatedly and read the remainders from the bottom up.

---
## 📄 Page 2: Geometry, Combinatorics & Probability

### 🏊 Triangles
| Point | Made by | Property |
|---|---|---|
| **Centroid** | medians | splits each median **2 : 1** |
| **Circumcenter** | perpendicular bisectors | equally far from the 3 vertices (radius **R**) |
| **Orthocenter** | altitudes | — |
| **Incenter** | angle bisectors | equally far from the 3 sides (radius **r**) |

- **Area:** ½ · base · height · ½ab sin C · **Heron:** s = (a + b + c)/2 → √(s(s − a)(s − b)(s − c)) · **L = r·s** · **R = abc / (4L)**
- **Angle bisector theorem:** BD / DC = AB / AC.
- **30-60-90:** sides 1 : √3 : 2 · **45-45-90:** sides 1 : 1 : √2 · **Similar** (ratio k): lengths × k, areas × k².

### 🎮 Circles
- **Inscribed angle = ½ the central angle** · an angle in a semicircle = 90°.
- **Cyclic quadrilateral:** opposite angles add up to **180°**.
- **Power of a point:** two chords PA·PB = PC·PD · tangent PT² = PA·PB.
- **Tangent ⟂ radius.** Two circles touching externally: distance between centres = r₁ + r₂ · internally: \|r₁ − r₂\|.

### 🏊 Transformations (about the origin)
| | Aturan |
|---|---|
| Reflect in the x-axis / y-axis / line y = x | (x, −y) / (−x, y) / (y, x) |
| Rotate 90° counter-clockwise / 180° / 270° | (−y, x) / (−x, −y) / (y, −x) |
| Translation (a, b) | (x + a, y + b) |
| Dilation, scale factor k | (kx, ky) · lengths × k · areas × k² |

### 🎮 Coordinate geometry
- **Distance** √((x₂ − x₁)² + (y₂ − y₁)²) · **midpoint** ((x₁ + x₂)/2, (y₁ + y₂)/2) · **slope** m = (y₂ − y₁)/(x₂ − x₁).
- **Line:** y = mx + c · parallel: same m · perpendicular: **m₁ m₂ = −1**.
- **Circle:** (x − h)² + (y − k)² = r².
- **Shoelace:** L = ½ \|Σ (xᵢ yᵢ₊₁ − xᵢ₊₁ yᵢ)\|, points listed in order around the polygon.

### 🍳 Solids
| Solid | Volume | Surface area |
|---|---|---|
| Prism | base × height | 2 · base + base perimeter × height |
| Cylinder | πr²h | 2πr² + 2πrh |
| Pyramid | ⅓ · base · height | base + the side faces |
| Cone | ⅓πr²h | πr² + πrℓ, ℓ = √(r² + h²) |
| Sphere | 4/3 πr³ | 4πr² |

### 🍳 Counting & combinatorics
- **Product rule** (steps one after another) · **sum rule** (choices that cannot happen together).
- **Inclusion-exclusion:** \|A ∪ B\| = \|A\| + \|B\| − \|A ∩ B\| · three sets: singles − pairs + triple overlap.
- **Pigeonhole:** n + 1 objects into n boxes → some box holds ≥ 2 · general: some box holds ≥ ⌈N/k⌉.
- **Permutations** P(n, k) = n!/(n − k)! · **Combinations** C(n, k) = n!/(k!(n − k)!) · C(n, k) = C(n, n − k) · C(n, k) = C(n − 1, k − 1) + C(n − 1, k) · ΣC(n, k) = 2ⁿ.
- **Stars and bars:** x₁ + … + xₖ = n → integers ≥ 0: **C(n + k − 1, k − 1)** · integers ≥ 1: **C(n − 1, k − 1)**.

### 🎮 Probability & 🏊 strategies
- P(A) = favourable outcomes / all outcomes (equally likely) · **P(not A) = 1 − P(A)**.
- P(A ∪ B) = P(A) + P(B) − P(A ∩ B) · independent: **P(A ∩ B) = P(A)·P(B)** · conditional: **P(A \| B) = P(A ∩ B) / P(B)**.
- **Strategies:** split into cases (*casework*) · "at least one" → **count the opposite** (*complementary counting*) · find a one-to-one pairing (*bijection*) · use symmetry.
