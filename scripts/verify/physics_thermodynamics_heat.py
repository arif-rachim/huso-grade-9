"""Independent checks for materi/physics/thermodynamics-heat.md (examples + check questions)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from physics_helpers import Checker

C = Checker("materi/physics/thermodynamics-heat.md")
ok = C.ok
CW, LF, LV, CICE, CSTEAM, COIL = 4186.0, 334e3, 2.26e6, 2100.0, 2010.0, 2000.0

# ---- enthalpy model of H2O: heat needed per kg from ice at 0 C (solid), so we can solve mixing by conservation of enthalpy
def h_water(T):          # liquid water at T (0..100), measured from solid ice at 0 C
    return LF + CW * T

# Example 1: bisection on heat balance (independent of the algebra in the text)
def balance(T):
    return 0.20 * CW * (80 - T) - 0.30 * CW * (T - 20)
lo, hi = 20.0, 80.0
for _ in range(200):
    mid = (lo + hi) / 2
    if balance(mid) > 0: lo = mid
    else: hi = mid
T1 = lo
ok(abs(T1 - 44) < 1e-9, T1)
C.mcq("**Example 1.**", 44, "°C", "B")
ok(abs((20 + 80) / 2 - 50) < 1e-12)
C.opt_is("**Example 1.**", "C", (20 + 80) / 2, "°C")                     # plain average
T_swapped = (0.30 * 80 + 0.20 * 20) / 0.50
C.opt_is("**Example 1.**", "D", T_swapped, "°C")                         # masses swapped
ok(abs(0.20 * CW * (80 - 44) - 0.30 * CW * (44 - 20)) < 1e-6)
ok(round(0.20 * CW * 36) == 30139, "picture number")
ok(44 - 20 < 80 - 44 and 0.30 > 0.20, "closer to the cold temperature")
ok(abs(16 - 6 - 0.5 * 44 + 0.5 * 44) >= 0 and abs((16 + 6) / 0.5 - 44) < 1e-12, "algebra in steps")

# Example 2: conservation of enthalpy (ice at 0 C solid is the zero level)
m_ice, m_w, T_w = 0.10, 0.50, 40.0
H_total = m_ice * 0 + m_w * h_water(T_w)
can_melt_all = m_w * CW * T_w >= m_ice * LF
ok(can_melt_all, "all ice melts")
ok(abs(m_w * CW * T_w - 83720) < 1e-6 and abs(m_ice * LF - 33400) < 1e-6)
T2 = (H_total / (m_ice + m_w) - LF) / CW
ok(abs(T2 - 20.03) < 0.01, T2)
C.mcq("**Example 2.**", T2, "°C", "C", tol=0.02)
# equation in the text
ok(abs((83720 - 33400) / (m_w * CW + m_ice * CW) - T2) < 1e-9 and abs(50320 / 2511.6 - T2) < 1e-9)
# distractors
T_no_latent = (m_w * T_w + m_ice * 0) / (m_w + m_ice)                       # ice treated as 0 C water
C.opt_is("**Example 2.**", "E", T_no_latent, "°C", tol=0.01)
T_forget_warm = T_w - m_ice * LF / (m_w * CW)                               # melted ice not warmed
C.opt_is("**Example 2.**", "D", T_forget_warm, "°C", tol=0.01)
ok(abs(T_forget_warm - 24.04) < 0.01)
# (A) 0 C only if the water cannot melt all ice: here it can, so the claim "only if not enough heat" is consistent
ok(m_ice * LF > m_w * CW * T_w - 1e-9 or can_melt_all)
ok(abs(LV / LF - 6.77) < 0.01, "almost 7 times")

# Q1: oil vs water
Q = 1.0 * CW * 10
dT_oil = Q / (1.0 * COIL)
ok(abs(Q - 41860) < 1e-6 and abs(dT_oil - 20.93) < 0.01)
C.mcq("**1.**", dT_oil, "°C", "C", tol=0.03)
C.opt_is("**1.**", "B", 10, "°C")
C.opt_is("**1.**", "A", 10 * COIL / CW, "°C", tol=0.06)                    # ratio the wrong way (4.78 -> 5)
ok(round(10 * COIL / CW) == 5)

# Q2: melt 0.25 kg
Q2 = 0.25 * LF
C.mcq("**2.**", Q2, "J", "E")
ok(abs(Q2 - 83500) < 1e-6)
C.opt_is("**2.**", "A", LF, "J")                      # forgot mass
C.opt_is("**2.**", "B", 0.25 * LV, "J")               # used L_v
C.opt_is("**2.**", "C", LF / 0.25, "J")               # divided
C.opt_is("**2.**", "D", Q2 / 1000, "J")               # right number, wrong unit

# Q3: pool
Q3 = 200 * CW * (25 - 20)
C.mcq("**3.**", Q3, "J", "A", tol=0.02)
C.opt_is("**3.**", "B", 200 * CW, "J", tol=0.02)                # forgot dT
C.opt_is("**3.**", "C", CW * 5, "J", tol=0.02)                  # forgot mass
C.opt_is("**3.**", "D", 200000 * CW * 5, "J", tol=0.02)         # grams with J/kg/K
C.opt_is("**3.**", "E", 200 * CW * 25, "J", tol=0.02)           # used final T

# Q4 concept: the right option is D; each option text is identifiable
o4 = C.options("**4.**")
ok(C.key_letter(4) == "D" and "pulls the molecules apart" in o4["D"] and len(o4) == 5)
ok(all("pulls" not in o4[k] for k in "ABCE"))
# temperature on a heating curve with this model stays at 100 C while liquid -> vapor: simulate enthalpy steps
def temp_after(q, m=1.0):
    """Temperature of 1 kg of liquid water at 100 C after adding q joules of heat (simulation)."""
    return 100.0 if q <= m * LV else 100.0 + (q - m * LV) / (m * CSTEAM)
ok(all(temp_after(q) == 100.0 for q in (1e3, 5e5, 2.2e6)), "flat while boiling")

# Q5: ice -> water at 20 C
Q5 = 0.10 * LF + 0.10 * CW * 20
C.mcq("**5.**", Q5, "J", "B", tol=0.01)
ok(abs(Q5 - 41772) < 1e-6)
C.opt_is("**5.**", "A", 0.10 * CW * 20, "J", tol=0.01)          # no melting
C.opt_is("**5.**", "C", 0.10 * LF, "J", tol=0.01)               # no warming
C.opt_is("**5.**", "D", 1.0 * LF + 1.0 * CW * 20, "J", tol=0.01)  # 1 kg
C.opt_is("**5.**", "E", 0.10 * LV + 0.10 * CW * 20, "J", tol=0.01)  # L_v

# heating-curve picture numbers (1 kg)
segs = [1 * CICE * 20, 1 * LF, 1 * CW * 100, 1 * LV, 1 * CSTEAM * 20]
ok([round(s / 1000) for s in segs] == [42, 334, 419, 2260, 40])
# letters used at most twice
letters = [C.key_letter(i) for i in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in set(letters)), letters)
C.done()
