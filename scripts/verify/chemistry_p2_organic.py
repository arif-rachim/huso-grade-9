"""Tiny organic-chemistry toolkit for the chemistry verify scripts (acyclic molecules only, no RDKit needed).

* parse(smiles)   : SMILES-like text -> Mol. Atoms C O N Br Cl F I S, branches ( ), bonds = and #. No rings, no stereo.
* canon(mol)      : canonical string of the molecule (tree), so two drawings of the same molecule compare equal.
* formula(mol)    : Hill-style formula with implicit hydrogens (valence 4/2/3/1).
* name(mol)       : IUPAC name from the rules (principal group, longest chain, lowest locants) for chains with alkyl,
                    halo and hydroxy side groups, one C=C or C#C, and -ol / -al / -one / -oic acid.
* classify(mol)   : set of functional groups present.
It is deliberately written from the nomenclature rules and not from the answer keys."""
import itertools, re

VAL = {"C": 4, "O": 2, "N": 3, "Br": 1, "Cl": 1, "F": 1, "I": 1, "S": 2}


class Mol:
    def __init__(self):
        self.lab, self.adj, self.order = {}, {}, {}

    def add(self, label, to=None, order=1):
        i = len(self.lab)
        self.lab[i] = label
        self.adj[i] = set()
        if to is not None:
            self.adj[i].add(to); self.adj[to].add(i)
            self.order[frozenset((i, to))] = order
        return i

    def bo(self, a, b):
        return self.order[frozenset((a, b))]

    def nH(self, i):
        return VAL[self.lab[i]] - sum(self.bo(i, j) for j in self.adj[i])


def parse(s):
    m = Mol()
    stack, prev, order = [], None, 1
    k = 0
    while k < len(s):
        ch = s[k]
        if ch == "(":
            stack.append(prev)
        elif ch == ")":
            prev = stack.pop()
        elif ch == "=":
            order = 2
        elif ch == "#":
            order = 3
        else:
            sym = s[k:k + 2] if s[k:k + 2] in ("Br", "Cl") else ch
            k += len(sym) - 1
            assert sym in VAL, sym
            prev = m.add(sym, prev, order)
            order = 1
        k += 1
    return m


def formula(m):
    cnt = {}
    for i, l in m.lab.items():
        cnt[l] = cnt.get(l, 0) + 1
        cnt["H"] = cnt.get("H", 0) + m.nH(i)
        assert m.nH(i) >= 0, "valence error"
    order = ["C", "H"] + sorted(k for k in cnt if k not in ("C", "H"))
    return "".join(k + (str(cnt[k]) if cnt[k] > 1 else "") for k in order if k in cnt)


def canon(m):
    deg = {i: len(a) for i, a in m.adj.items()}
    left = set(m.adj)
    leaves = [i for i in left if deg[i] <= 1]
    while len(left) > 2:
        nxt = []
        for l in leaves:
            left.discard(l)
            for nb in m.adj[l]:
                if nb in left:
                    deg[nb] -= 1
                    if deg[nb] == 1:
                        nxt.append(nb)
        leaves = nxt

    def enc(v, parent):
        kids = sorted(str(m.bo(v, w)) + enc(w, v) for w in m.adj[v] if w != parent)
        return "(" + m.lab[v] + "".join(kids) + ")"
    return min(enc(c, None) for c in left)


# ------------------------------------------------------------------ functional groups
def classify(m):
    g = set()
    for i, l in m.lab.items():
        nb = m.adj[i]
        if l == "O":
            if len(nb) == 1:
                (c,) = nb
                if m.lab[c] == "C":
                    if m.bo(i, c) == 2:
                        others = [x for x in m.adj[c] if x != i]
                        heteros = [x for x in others if m.lab[x] in ("O", "N")]
                        if any(m.lab[x] == "O" and len(m.adj[x]) == 1 for x in heteros):
                            g.add("carboxylic acid")
                        elif any(m.lab[x] == "O" for x in heteros):
                            g.add("ester")
                        elif any(m.lab[x] == "N" for x in heteros):
                            g.add("amide")
                        elif any(m.lab[x] in ("Cl", "Br") for x in others):
                            g.add("acyl halide")
                        elif sum(1 for x in others if m.lab[x] == "C") == 2:
                            g.add("ketone")
                        else:
                            g.add("aldehyde")
                    else:
                        c_has_carbonyl = any(m.lab[x] == "O" and m.bo(c, x) == 2 for x in m.adj[c])
                        if not c_has_carbonyl:
                            g.add("alcohol")
            elif len(nb) == 2 and all(m.lab[x] == "C" for x in nb):
                if any(any(m.lab[y] == "O" and m.bo(x, y) == 2 for y in m.adj[x]) for x in nb):
                    pass  # ester oxygen, counted above
                else:
                    g.add("ether")
        if l == "N" and len(nb) >= 1 and not any(m.lab[x] == "C" and any(m.lab[y] == "O" and m.bo(x, y) == 2 for y in m.adj[x]) for x in nb):
            g.add("amine")
        if l in ("Br", "Cl", "F", "I"):
            g.add("alkyl halide")
    for (a, b), o in ((tuple(k), o) for k, o in m.order.items()):
        if m.lab[a] == "C" and m.lab[b] == "C":
            if o == 2:
                g.add("alkene")
            if o == 3:
                g.add("alkyne")
    return g


# ------------------------------------------------------------------ naming
STEM = ["meth", "eth", "prop", "but", "pent", "hex", "hept", "oct", "non", "dec"]
HALO = {"Br": "bromo", "Cl": "chloro", "F": "fluoro", "I": "iodo"}
MULT = {1: "", 2: "di", 3: "tri", 4: "tetra"}


def _carbon_paths(m):
    cs = [i for i in m.lab if m.lab[i] == "C"]
    if len(cs) == 1:
        return [[cs[0]]]
    out = []
    for a, b in itertools.combinations(cs, 2):
        stack = [(a, [a])]
        while stack:
            v, p = stack.pop()
            if v == b:
                out.append(p); break
            for w in m.adj[v]:
                if w not in p and m.lab[w] == "C":
                    stack.append((w, p + [w]))
    return out


def _branch_name(m, c, root):
    """Name of an alkyl branch starting at carbon c (attached to root); straight chains only."""
    size, prev, cur = 0, root, c
    while True:
        size += 1
        nxt = [w for w in m.adj[cur] if w != prev]
        assert all(m.lab[w] == "C" and m.bo(cur, w) == 1 for w in nxt), "unsupported side group"
        if not nxt:
            break
        assert len(nxt) == 1, "branched side chain not supported"
        prev, cur = cur, nxt[0]
    return {1: "methyl", 2: "ethyl", 3: "propyl", 4: "butyl"}[size]


def name(m):
    cls = classify(m)
    # principal group: carbon bearing it
    prin = None
    for key, suffix in (("carboxylic acid", "oic acid"), ("aldehyde", "al"), ("ketone", "one"), ("alcohol", "ol")):
        if key in cls:
            prin = (key, suffix)
            break

    def pg_carbons(key):
        res = []
        for i, l in m.lab.items():
            if l != "O":
                continue
            (c,) = list(m.adj[i]) if len(m.adj[i]) == 1 else (None,)
            if c is None:
                continue
            if key == "alcohol" and m.bo(i, c) == 1 and not any(m.lab[x] == "O" and m.bo(c, x) == 2 for x in m.adj[c]):
                res.append(c)
            if key in ("ketone", "aldehyde", "carboxylic acid") and m.bo(i, c) == 2:
                res.append(c)
        return res
    pgc = pg_carbons(prin[0]) if prin else []
    multi = [(a, b) for k, o in m.order.items() if o >= 2 for a, b in [tuple(k)] if m.lab[a] == "C" and m.lab[b] == "C"]
    paths = _carbon_paths(m)

    def covers(p):
        ok_ = all(c in p for c in pgc)
        if multi:
            ok_ = ok_ and all(a in p and b in p for a, b in multi)
        return ok_
    elig = [p for p in paths if covers(p)]
    longest = max(len(p) for p in elig)
    best = None
    for p in elig:
        if len(p) < longest:
            continue
        for chain in (p, p[::-1]):
            pos = {c: k for k, c in enumerate(chain, 1)}
            pg = sorted(pos[c] for c in pgc)
            mu = sorted(min(pos[a], pos[b]) for a, b in multi)
            subs = []
            bad = False
            for c in chain:
                for nb in m.adj[c]:
                    if nb in pos:
                        continue
                    if m.lab[nb] in HALO:
                        subs.append((pos[c], HALO[m.lab[nb]]))
                    elif m.lab[nb] == "O" and not (prin and nb in [x for cc in pgc for x in m.adj[cc] if m.lab[x] == "O"]):
                        subs.append((pos[c], "hydroxy"))
                    elif m.lab[nb] == "C":
                        try:
                            subs.append((pos[c], _branch_name(m, nb, c)))
                        except AssertionError:
                            bad = True      # a substituted side chain (e.g. bromomethyl): another chain choice is better
            if bad:
                continue
            key = (-len(subs), pg, mu, sorted(s[0] for s in subs), sorted(subs, key=lambda s: s[1]))
            if best is None or key < best[0]:
                best = (key, chain, pg, mu, subs)
    _, chain, pg, mu, subs = best
    n = len(chain)
    groups = {}
    for p_, nm in subs:
        groups.setdefault(nm, []).append(p_)
    pre = "-".join(",".join(map(str, sorted(groups[nm]))) + "-" + MULT[len(groups[nm])] + nm for nm in sorted(groups))
    stem = STEM[n - 1]
    tripl = any(m.bo(a, b) == 3 for a, b in multi)
    core = "yn" if tripl else "en" if multi else "an"
    show_mu = multi and (n >= 4 or prin)
    unsat_part = stem + (("-" + str(mu[0]) + "-") if show_mu else "") + core
    if not prin:
        body = unsat_part + "e"
    else:
        loc = ("-" + ",".join(map(str, pg)) + "-") if key_needs_locant(prin[0], n, pg) or multi else ""
        body = unsat_part + loc + prin[1]
    return pre + body


def key_needs_locant(kind, n, pg):
    if kind in ("aldehyde", "carboxylic acid"):
        return False
    if kind == "alcohol":
        return n >= 3
    if kind == "ketone":
        return n >= 5
    return True


if __name__ == "__main__":
    tests = {"CCCCC": "pentane", "CC(O)CC(C)C": "4-methylpentan-2-ol", "CCC(C)CCC": "3-methylhexane", "CC(C)=CC": "2-methylbut-2-ene",
             "CC(Br)(C)CC": "2-bromo-2-methylbutane", "CC(=O)C": "propanone", "CCC=O": "propanal", "CC(=O)O": "ethanoic acid",
             "CCO": "ethanol", "CC=C": "propene", "C=CC(C)C": "3-methylbut-1-ene", "CCC(=O)CC": "pentan-3-one", "CC(O)C": "propan-2-ol",
             "CC#CC": "but-2-yne", "CC=CCO": "but-2-en-1-ol"}
    for smi, want in tests.items():
        got = name(parse(smi))
        print("OK " if got == want else "BAD", smi, got, want)
    print(formula(parse("CC(=O)O")), formula(parse("COC")))
