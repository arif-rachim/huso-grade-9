#!/usr/bin/env python3
"""Independently re-solve every physics question in content/questions/physics.json.

Each answer is recomputed from the numbers in the stem (no use of the key), then compared with
the choice the file marks as correct. Distractors must NOT match the computed value.
Run from the repo root:  python3 scripts/verify/content_physics.py
Exit code 0 = every answer re-derived and no letter is used for more than 30 % of the keys.
"""
import json
import math
import re
import sys
from collections import Counter

g = 9.8
sin = lambda d: math.sin(math.radians(d))
cos = lambda d: math.cos(math.radians(d))


def bisect(f, lo, hi):
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def n(v):
    return ("n", v)


def s(text):
    return ("s", text)


def series():
    E = []
    # ---- 1-8 kinematics
    E.append(n(2 * 12))
    E.append(n(24 / 6))
    E.append(n(g * 3.0))
    v = 5 * 2.0
    E.append(n(0.5 * 5 * 2.0 ** 2 + v * 3.0))
    E.append(n(14.7 ** 2 / (2 * g)))
    E.append(n((50 + 50) / (20 + 40)))
    E.append(n(bisect(lambda t: t * t - (100 + 20 * t), 1, 100)))  # B: ½·2·t², A: 100 + 20t
    E.append(n(bisect(lambda t: 25 + 20 * t - 0.5 * g * t * t, 0.1, 50)))
    # ---- 9-16 dynamics
    E.append(n(4.0 * 3.0))
    E.append(n(2.0 * g))
    E.append(n(50 - 10 * 3.0))
    E.append(n(450 * 0.40 / 60))
    E.append(n(g * sin(30)))
    E.append(n(70 * (g + 2.0)))
    m1, m2 = 3.0, 5.0
    a = (m2 - m1) * g / (m1 + m2)
    E.append(n(m1 * (g + a)))
    E.append(n(g * (sin(30) - 0.20 * cos(30))))
    # ---- 17-24 conservation
    E.append(n(0.5 * 2.0 * 3.0 ** 2))
    E.append(n(55 * g * 3.0 / 1000))
    E.append(n(1.0 * 4.0 / (1.0 + 3.0)))
    E.append(n(math.sqrt(2 * g * 5.0)))
    E.append(n(80 * 5.0 / (80 + 60)))
    E.append(n(1500 * 3.0 * 60 / 1000))
    k, m, v0 = 200, 2.0, 6.0
    E.append(n(bisect(lambda x: 0.5 * k * x * x - 0.5 * m * v0 * v0, 0, 10)))
    vb = 0.010 * 400 / 2.00
    E.append(n(bisect(lambda h: 2.00 * g * h - 0.5 * 2.00 * vb * vb, 0, 10)))
    # ---- 25-32 circular motion and rotation
    E.append(n(4.0 ** 2 / 2.0))
    E.append(n(1 / 5.0))
    E.append(n(2.0 ** 2 / 0.10))
    E.append(n(0.30 * 20 * sin(30)))
    E.append(n(math.sqrt(0.50 * g * 20)))
    I = 0.5 * 2.0 * 0.25 ** 2
    E.append(n(0.25 / I))
    E.append(n(0.50 * 5.0 ** 2 / 1.0 - 0.50 * g))
    I1, w1, I2 = 3.0, 2.0, 1.2
    w2 = I1 * w1 / I2
    E.append(n((0.5 * I2 * w2 ** 2) / (0.5 * I1 * w1 ** 2)))
    # ---- 33-40 SHM
    E.append(n(50 * 0.20))
    E.append(n(30 / 12))
    E.append(n(2 * math.pi * math.sqrt(1.0 / g)))
    E.append(n(2 * math.pi * math.sqrt(0.50 / 200)))
    E.append(n(math.sqrt(4)))
    E.append(n(0.10 * 4.0))
    w = math.sqrt(100 / 0.40)
    E.append(n(w * math.sqrt(0.10 ** 2 - 0.060 ** 2)))
    L = g * (2.0 / (2 * math.pi)) ** 2
    E.append(n(2 * math.pi * math.sqrt(L / (g + g / 4))))
    # ---- 41-48 gravity
    f = 1 / 2 ** 2
    E.append(s({0.5: "Half as large", 0.25: "One quarter as large", 1: "The same", 2: "Twice as large", 4: "Four times as large"}[f]))
    E.append(n(2.0 * g))
    E.append(n(70 * 1.6))
    r = bisect(lambda r: 1 / r ** 2 - 0.25, 0.5, 10)
    E.append(s(f"{round(r)}R"))
    E.append(n(g * (4 / 2 ** 2)))
    G, M, rr = 6.674e-11, 5.97e24, 6.77e6
    E.append(n(math.sqrt(G * M / rr) / 1000))
    E.append(n(4 ** 1.5))
    E.append(n(bisect(lambda x: 1 / x ** 2 - (1 / 81) / (1 - x) ** 2, 0.2, 0.999)))
    # ---- 49-56 circuits
    E.append(n(12 / 6.0))
    E.append(n(1200 / 120))
    E.append(n(4.0 + 4.0))
    Rt = 1 / (1 / 8.0 + 1 / 24.0)
    E.append(n(24 / Rt))
    E.append(n(2.0 * (3.0 / 60)))
    E.append(n(0.5 * 10e-6 * 12 ** 2 * 1000))
    Rp = 1 / (1 / 6.0 + 1 / 12.0)
    I_tot = 12 / (4.0 + Rp)
    Vp = I_tot * Rp
    E.append(n(Vp ** 2 / 12.0))
    Ceq = 1 / (1 / 6.0 + 1 / 3.0)
    E.append(n(Ceq * 9.0))
    # ---- 57-64 laws of thermodynamics
    E.append(n(500 - 200))
    E.append(s("The second law"))
    E.append(n(25 + 273))
    E.append(n((1 - 300 / 500) * 100))
    E.append(n(800 - 200))
    E.append(n(-40 - (-150)))
    carnot = (1 - 300 / 400) * 100
    claimed = 300 / 1000 * 100
    assert claimed > carnot
    E.append(s("Impossible: 30% is above the Carnot limit of 25%"))
    E.append(n(300 / (1 - 0.60)))
    # ---- 65-72 heat
    E.append(n(0.50 * 4186 * (100 - 20) / 1000))
    E.append(s("Radiation"))
    E.append(n(1000 * 4186 * 1.0 / 1e6))
    E.append(n(0.30 * 3.34e5 / 1000))
    E.append(n((0.200 * 80 + 0.300 * 20) / 0.500))
    E.append(n(10 / 20))
    E.append(n((0.10 * 2100 * 10 + 0.10 * 3.34e5 + 0.10 * 4186 * 100) / 1000))
    E.append(n(2.0 * 4186 * (22 - 20) / (0.50 * (200 - 22))))
    # ---- 73-80 ideal gas
    E.append(n(600 / 300))
    E.append(n(100 * 450 / 300))
    E.append(n(100 * 2.0 / 0.50))
    E.append(n(1.0e5 * 2.0e-3 / (8.315 * 300)))
    E.append(n(2.0 * 3.0 / 1.0))
    E.append(n(2.0e5 * (4.0 - 1.0) * 1e-3))
    E.append(n(300 * 3 * 0.5))
    W = 400
    dU = 1.5 * W
    E.append(n(W + dU))
    # ---- 81-88 sound
    E.append(n(343 / 440))
    E.append(s("Frequency"))
    E.append(n(343 * 0.40 / 2))
    E.append(n(37 / 1480))
    E.append(n(10 ** ((90 - 60) / 10)))
    E.append(n(331 + 0.6 * 30))
    E.append(n(343 / (4 * 0.25)))
    E.append(n(343 * 0.50 / 2 + 343 * 1.20 / 2))
    return E


NUM = re.compile(r"[-+]?\d+(?:\.\d+)?")


def parse(text):
    m = NUM.search(text.replace("−", "-"))
    if not m:
        return None, 0
    tok = m.group(0)
    dec = len(tok.split(".")[1]) if "." in tok else 0
    return float(tok), dec


def tolerance(val, dec):
    if dec > 0:
        return 0.5 * 10 ** -dec + 1e-9
    return max(0.5, 0.005 * abs(val))


def main():
    data = json.load(open("content/questions/physics.json", encoding="utf-8"))["questions"]
    exp = series()
    errors = []
    if len(exp) != len(data):
        print(f"FAIL: {len(exp)} recomputed answers but {len(data)} questions")
        return 1
    for q, (kind, val) in zip(data, exp):
        qid = q["id"]
        key = q["choices"][q["answer"]]
        others = [t for c, t in q["choices"].items() if c != q["answer"]]
        if kind == "s":
            if key != val:
                errors.append(f"{qid}: key text {key!r} != recomputed {val!r}")
            if val in others:
                errors.append(f"{qid}: correct text also appears as a distractor")
            continue
        kv, kd = parse(key)
        if kv is None or abs(kv - val) > tolerance(kv, kd):
            errors.append(f"{qid}: key {key!r} but recomputed {val:.5g}")
        for t in others:
            ov, od = parse(t)
            if ov is not None and abs(ov - val) <= tolerance(ov, od):
                errors.append(f"{qid}: distractor {t!r} also matches {val:.5g}")
    counts = Counter(q["answer"] for q in data)
    worst = max(counts.values()) / len(data)
    print("answer letters:", dict(sorted(counts.items())), f"(max share {worst:.0%})")
    if worst > 0.30:
        errors.append("one answer letter is used for more than 30% of the questions")
    for e in errors:
        print("FAIL:", e)
    if not errors:
        print(f"OK: all {len(data)} answers re-derived independently")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
