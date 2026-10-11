"""Independent checks for materi/physics/electromagnetism-circuits.md: resistors, power, batteries, capacitors.

Every worked example and every Check answer is recomputed here with a different method
(simulation, brute force, vector formulas) and every distractor note of the answer key is
reproduced by the wrong calculation it names."""
import pathlib, re, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/physics/electromagnetism-circuits.md").read_text()
n = 0
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1


def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    return dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))


def first_number(s):
    s = re.sub(r"\s*×\s*10", "e", s.replace("−", "-")).translate(SUP)
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s)
    m = re.search(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", s)
    return m.group(0)


def matches(opt_text, value):
    """True if value rounds to the number printed in the option (same number of decimals)."""
    tok = first_number(opt_text)
    mant = tok.split("e")[0]
    exp = int(tok.split("e")[1]) if "e" in tok else 0
    dec = len(mant.split(".")[1]) if "." in mant else 0
    scale = 10 ** exp
    return abs(value / scale - float(mant)) <= 0.5 * 10 ** (-dec) + 1e-9


def letters(label, value):
    o = options(label)
    return [k for k, v in o.items() if matches(v, value)]


def mcq(label, value, key):
    o = options(label)
    ok(len(set(o.values())) == 5, "options distinct")
    ok(letters(label, value) == [key], f"{label}: {letters(label, value)} vs {key} for {value}")


def claim(label, value, letter):
    """A distractor note in the key: this wrong path must give exactly that option."""
    ok(letters(label, value) == [letter], f"{label} claim {letter}: got {letters(label, value)} for {value}")


def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", TXT.split("<details>")[1], re.M).group(1)


def finish(keys):
    got = [key_letter(q) for q in range(1, 6)]
    ok(got == keys, f"keys {got} vs {keys}")
    ok(max(got.count(c) for c in "ABCDE") <= 2, "a letter is used more than twice")
    print(f"OK {n} checks")


from fractions import Fraction as Fr

def solve_network(known, edges):
    """Nodal analysis with exact fractions.
    known: {node: voltage}; edges: [(node_a, node_b, conductance)] (a conductance is 1/R, or C for a capacitor in charge terms).
    Returns {node: voltage}. Unknown nodes satisfy: sum of g * (V_node - V_other) = 0."""
    nodes = sorted({a for a, b, g in edges} | {b for a, b, g in edges})
    unk = [x for x in nodes if x not in known]
    idx = {x: i for i, x in enumerate(unk)}
    N = len(unk)
    M = [[Fr(0)] * (N + 1) for _ in range(N)]
    for a, b, g in edges:
        for p, q in ((a, b), (b, a)):
            if p in idx:
                M[idx[p]][idx[p]] += g
                if q in idx: M[idx[p]][idx[q]] -= g
                else: M[idx[p]][N] += g * known[q]
    for c in range(N):                      # Gauss-Jordan elimination
        piv = next(r for r in range(c, N) if M[r][c] != 0)
        M[c], M[piv] = M[piv], M[c]
        M[c] = [v / M[c][c] for v in M[c]]
        for r in range(N):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    V = dict(known)
    for x in unk: V[x] = M[idx[x]][N]
    return V

def flow(V, a, b, g):
    """Current (or charge) through an element from a to b."""
    return g * (V[a] - V[b])

# ---------- picture: series and parallel, 6 and 3 ohm on 12 V ----------
V = solve_network({"+": Fr(12), "-": Fr(0)}, [("+", "m", Fr(1, 6)), ("m", "-", Fr(1, 3))])      # series
I_series = flow(V, "+", "m", Fr(1, 6))
ok(I_series == Fr(4, 3) and abs(float(I_series) - 1.3) < 0.04)
ok(V["+"] - V["m"] == 8 and V["m"] - V["-"] == 4)        # 8 V + 4 V = 12 V
Vp = solve_network({"+": Fr(12), "-": Fr(0)}, [("+", "-", Fr(1, 6)), ("+", "-", Fr(1, 3))])
I6, I3 = flow(Vp, "+", "-", Fr(1, 6)), flow(Vp, "+", "-", Fr(1, 3))
ok((I6, I3, I6 + I3) == (2, 4, 6))
ok(Fr(12) / (I6 + I3) == 2)           # equivalent resistance 2 ohm
ok(1 / (Fr(1, 6) + Fr(1, 3)) == 2 and 6 + 3 == 9)

# ---------- Example 1 ----------
V = solve_network({"+": Fr(12), "-": Fr(0)}, [("+", "b", Fr(1, 6)), ("b", "-", Fr(1, 6)), ("b", "-", Fr(1, 3))])
I_tot = flow(V, "+", "b", Fr(1, 6))
I_R2 = flow(V, "b", "-", Fr(1, 6)); I_R3 = flow(V, "b", "-", Fr(1, 3))
ok(I_tot == Fr(3, 2) and I_R2 == Fr(1, 2) and I_R3 == 1 and V["b"] == 3 and V["+"] - V["b"] == 9)
ok(I_R2 + I_R3 == I_tot)
mcq("**Example 1.**", float(I_R3), "B")
claim("**Example 1.**", float(I_tot), "C")      # total current
claim("**Example 1.**", float(I_R2), "A")       # R2 branch
claim("**Example 1.**", 12 / 6, "D")            # full battery voltage on 6 ohm
claim("**Example 1.**", 12 / 3, "E")            # full battery voltage on R3
ok(Fr(12, 8) == I_tot, "R = 6 + 2 = 8")

# ---------- Example 2 and the kitchen picture ----------
V_mains, P_toast, P_kettle = 220, 880, 1760
# find each resistance from P = V^2/R, then the currents from V = I R (not from P = IV)
R_toast, R_kettle = Fr(V_mains**2, P_toast), Fr(V_mains**2, P_kettle)
Vk = solve_network({"+": Fr(V_mains), "-": Fr(0)}, [("+", "-", 1 / R_toast), ("+", "-", 1 / R_kettle)])
i_t, i_k = flow(Vk, "+", "-", 1 / R_toast), flow(Vk, "+", "-", 1 / R_kettle)
ok((i_t, i_k) == (4, 8) and i_t + i_k == 12)
mcq("**Example 2.**", float(i_t + i_k), "D")
claim("**Example 2.**", float(i_t), "A")
claim("**Example 2.**", float(i_k), "C")
claim("**Example 2.**", float((i_t + i_k) / 2), "B")
claim("**Example 2.**", float(i_t * i_k), "E")
ok(i_t + i_k > 10 and i_k < 10, "both trip a 10 A breaker, the kettle alone does not")
ok(abs(1760 / 1000 * (3 / 60) - 0.088) < 1e-12, "kWh in the picture")

# ---------- core idea numbers ----------
rho_cu = 1.68e-8
ok(abs(rho_cu * 10 / 1e-6 - 0.17) < 0.005, "10 m copper wire, 1 mm^2")
# energy of a capacitor by adding up V dq while charging: V = q / C
C_, V_ = 10e-6, 6.0
steps = 100000
dq = C_ * V_ / steps
U = sum(((i + 0.5) * dq / C_) * dq for i in range(steps))
ok(abs(U - 180e-6) < 1e-9 and abs(0.5 * C_ * V_**2 - 180e-6) < 1e-12)

# ---------- Q1 ----------
def res(rho, L, A): return rho * L / A
R0 = res(1.0, 3.0, 2.0)
r_second = res(1.0, 2 * 3.0, 2 * 2.0)
ok(abs(r_second / R0 - 1) < 1e-12)
mult = {"A": 0.25, "B": 0.5, "C": 1.0, "D": 2.0, "E": 4.0}
o = options("**1.**")
parsed = {}
for k, t in o.items():
    t = t.strip()
    parsed[k] = 1.0 if t == "R" else (float(t[0]) if t.endswith("R") and t[0].isdigit() else (1 / float(t.split("/")[1]) if t.startswith("R/") else None))
ok(parsed == mult, parsed)
ok([k for k, v in parsed.items() if abs(v - r_second / R0) < 1e-12] == ["C"])
ok(abs(res(1.0, 6.0, 2.0) / R0 - 2) < 1e-12)             # D: length only
ok(abs(res(1.0, 3.0, 4.0) / R0 - 0.5) < 1e-12)           # B: area only
ok(abs(res(1.0, 6.0, 1.0) / R0 - 4) < 1e-12)             # E: area wrongly makes R bigger (halves A)
ok(abs(res(1.0, 1.5, 4.0) / R0 - 0.25) < 1e-12)          # A: length wrongly makes R smaller (halves L)

# ---------- Q2 ----------
V2 = solve_network({"+": Fr(12), "-": Fr(0)}, [("+", "-", Fr(1, 12)), ("+", "-", Fr(1, 4))])
I2 = flow(V2, "+", "-", Fr(1, 12)) + flow(V2, "+", "-", Fr(1, 4))
ok(I2 == 4)
mcq("**2.**", float(I2), "E")
claim("**2.**", 12 / (12 + 4), "A")       # series
claim("**2.**", 12 / 12, "B")             # 12 ohm branch only
claim("**2.**", 12 / ((12 + 4) / 2), "C") # average resistance 8 ohm
claim("**2.**", 12 / 4, "D")              # 4 ohm branch only

# ---------- Q3 ----------
# find R so that the power V^2/R is 1100 W (bisection), then the current from V = I R
lo, hi = 1.0, 1000.0
for _ in range(200):
    mid = (lo + hi) / 2
    if 220**2 / mid > 1100: lo = mid
    else: hi = mid
R3 = (lo + hi) / 2
I3_ = 220 / R3
ok(abs(R3 - 44) < 1e-9 and abs(I3_ - 5) < 1e-9 and abs(I3_**2 * R3 - 1100) < 1e-6 and abs(220 * I3_ - 1100) < 1e-6)
mcq("**3.**", R3, "C")
claim("**3.**", 1100 / 220**2, "A")
claim("**3.**", I3_, "B")
claim("**3.**", 220.0, "D")
claim("**3.**", 1100 * 220, "E")

# ---------- Q4 ----------
V4 = solve_network({"a": Fr(3, 1), "-": Fr(0)}, [("a", "-", Fr(1, 3))])      # two 1.5 V cells in series: the top is at 3.0 V
ok(flow(V4, "a", "-", Fr(1, 3)) == 1)
mcq("**4.**", 1.0, "B")
claim("**4.**", 1.5 / 3.0, "A")           # one battery
claim("**4.**", 1.5, "C")                 # voltage read as current
claim("**4.**", 3.0, "D")                 # total voltage read as current
claim("**4.**", 1.5 * 3.0, "E")
ok(Fr(3, 2) + Fr(3, 2) == 3)

# ---------- Q5 (capacitors by charge balance on the middle node) ----------
Vc = solve_network({"+": Fr(8), "-": Fr(0)}, [("+", "m", Fr(4)), ("m", "-", Fr(12))])   # conductance plays the role of C (in uF)
Q4 = flow(Vc, "+", "m", Fr(4))
Q12 = flow(Vc, "m", "-", Fr(12))
ok(Q4 == Q12 == 24 and Vc["+"] - Vc["m"] == 6 and Vc["m"] - Vc["-"] == 2)
mcq("**5.**", float(Q4), "B")
claim("**5.**", float((Fr(1, 4) + Fr(1, 12)) * 8), "A")     # reciprocals not flipped back
claim("**5.**", 4 * 8, "C")
claim("**5.**", 12 * 8, "D")
claim("**5.**", (4 + 12) * 8, "E")
# picture numbers: 6 uF and 3 uF in series on 12 V; parallel on 12 V
Vs = solve_network({"+": Fr(12), "-": Fr(0)}, [("+", "m", Fr(6)), ("m", "-", Fr(3))])
ok(flow(Vs, "+", "m", Fr(6)) == 24 and Vs["+"] - Vs["m"] == 4 and Vs["m"] == 8)
ok(6 * 12 == 72 and 3 * 12 == 36 and 72 + 36 == 108 and 9 * 12 == 108 and 1 / (Fr(1, 6) + Fr(1, 3)) == 2)

finish(['C', 'E', 'C', 'B', 'B'])
