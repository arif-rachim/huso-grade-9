# 🟥 HUSO Physics Cheat Sheet, Grade 9–10

> 🖨️ Print 2 pages (Ctrl+P). The exam gives you a **reference sheet** (constants + a list of formulas), but you must know **when and how** to use each formula, and a few useful ones are *not* on the sheet. Learn all of these. Use g = 9.8 m/s² unless the question says otherwise. A scientific calculator is allowed in Round 1.

---
## 📄 Page 1: Mechanics

### Constants given on the official sheet
| Name | Value | Name | Value |
|---|---|---|---|
| Gravitational constant G | 6.674 × 10⁻¹¹ N·m²/kg² | Speed of light c | 2.998 × 10⁸ m/s |
| Universal gas constant R | 8.315 J/(mol·K) | Avogadro's number N_A | 6.022 × 10²³ /mol |
| Speed of sound in dry air | 343 m/s | Elementary charge e | 1.602 × 10⁻¹⁹ C |
| Permittivity ε₀ | 8.854 × 10⁻¹² C²/(N·m²) | Permeability μ₀ | 4π × 10⁻⁷ T·m/A |
| Mass of proton / neutron | 1.673 / 1.675 × 10⁻²⁷ kg | Mass of electron | 9.109 × 10⁻³¹ kg |

### Kinematics (constant acceleration)
| Formula | Use it when |
|---|---|
| v = v₀ + at | you know time, not distance |
| x = x₀ + v₀t + ½at² | you know time, not final speed |
| v² = v₀² + 2a(x − x₀) | you know distance, not time |
| average speed = total distance ÷ total time | (not the average of two speeds!) |

- **Graphs:** slope of x–t = velocity · slope of v–t = acceleration · **area** under v–t = displacement.
- **Free fall:** a = 9.8 m/s² downward · from rest: v = gt, d = ½gt².
- **Vectors:** components v_x = v cos θ, v_y = v sin θ · combine with Pythagoras: R = √(x² + y²). Scalars: distance, speed, mass, energy.

### Dynamics
- **Newton 1:** no net force → constant velocity · **Newton 2:** **F_net = ma** · **Newton 3:** forces come in equal and opposite pairs *on different objects*.
- **Weight** W = mg · **friction** f = μN (static ≤ μ_sN, kinetic = μ_kN) · on an incline: along the slope **mg sin θ**, into the slope **mg cos θ**.
- **Two masses on a pulley:** a = (m₂ − m₁)g / (m₁ + m₂).
- **Free body diagram first:** draw all forces on **one** object, then F_net = ma along each direction.

### Energy and momentum
| Quantity | Formula |
|---|---|
| Work | W = Fd cos θ |
| Kinetic energy | KE = ½mv² |
| Gravitational PE | U_g = mgh |
| Spring PE | U_k = ½kx² |
| Power | P = W/t |
| Momentum / impulse | p = mv · Ft = Δp |

- **Conservation of energy:** KE + PE (+ heat) stays constant. **Momentum** is conserved in every collision (no external force); **kinetic energy** only in elastic ones.
- **Angular momentum:** L = Iω. No external torque → L constant (arms in → spin faster).

### Circular motion and rotation
- **Uniform circular motion:** v = 2πr/T · **a = v²/r** toward the center · centripetal force F = mv²/r (it is a *name* for the net force, not a new force).
- **Rotation:** ω = 2πf = 2π/T · **torque** τ = rF sin θ · **τ = Iα**.
- **Moments of inertia (sheet):** ring **mr²** · disk **½mr²** · stick about its center **ml²/12** · parallel axis **I = I₀ + md²** (so a stick about its end is ml²/3).

---
## 📄 Page 2: Oscillations, gravity, electricity, heat, sound

### Simple harmonic motion
- **Spring:** F = −kx · **T = 2π√(m/k)** · f = 1/T = ω/2π.
- **Pendulum:** **T = 2π√(L/g)** (small swings; mass does *not* matter) · energy swaps KE ↔ PE.

### Gravity
- **F = G m₁m₂ / r²** · **g = GM/r²** · double the distance → **¼** of the force.
- **Circular orbit:** gravity provides the centripetal force: GMm/r² = mv²/r → **v = √(GM/r)**.

### Circuits
| Idea | Formula |
|---|---|
| Current / Ohm's law | I = q/t · **V = IR** |
| Resistance of a wire | R = ρL/A |
| Series resistors | R_eq = R₁ + R₂ + … (same current) |
| Parallel resistors | 1/R_eq = 1/R₁ + 1/R₂ + … (same voltage) |
| Power / energy | P = IV = I²R = V²/R · E = Pt |
| Capacitor | C = Q/V · parallel: C₁ + C₂ · series: 1/C = 1/C₁ + 1/C₂ |

### Heat and gases
- **Q = mcΔT** · **heat capacity** C = mc · **phase change Q = mL** (temperature stays constant).
- Typical values (a question normally gives them): water c = 4186 J/(kg·K) · ice ≈ 2100 · steam ≈ 2010 · L_fusion (ice) = 334 kJ/kg · L_vaporization (water) = 2.26 MJ/kg.
- **Calorimetry:** heat lost by hot = heat gained by cold → find the final temperature.
- **Transfer:** conduction (touch) · convection (moving fluid) · radiation (waves, no matter needed).
- **Ideal gas:** **PV = nRT** (T in **kelvin**: K = °C + 273) · constant T: P₁V₁ = P₂V₂ · constant P: V/T constant · constant V: P/T constant.
- **Work by a gas:** W = PΔV (constant P) = **area under the P–V curve** · expanding gas does positive work.

### Laws of thermodynamics
- **0th:** two things in equilibrium with a third have the same temperature.
- **1st:** **ΔU = Q − W** (Q in, W done *by* the gas).
- **2nd:** heat flows hot → cold by itself · entropy of an isolated system never decreases · no engine is 100 % efficient · efficiency e = W/Q_hot.
- **3rd:** absolute zero (0 K) can never be reached.

### Sound
- **Longitudinal wave** (compressions and rarefactions) · needs a medium · **v = λf** · f = 1/T · v_air = 343 m/s (faster in liquids and solids).
- **Pitch** ↔ frequency · **loudness** ↔ amplitude / intensity · echo: distance = v·t / 2.
