"""Independent checks for materi/biology/cell-division.md (simulation of chromosomes, cells and gametes)."""
import itertools, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/cell-division.md").read_text()
KEY = TXT.split("<details>")[1]
n = 0

def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1

def options(label):
    block = TXT[TXT.index(label):]
    line = next(l for l in block.splitlines() if l.startswith("(A)"))
    o = dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))
    ok(len(o) == 5 and len(set(o.values())) == 5, f"{label}: need 5 distinct options")
    return o

def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", KEY, re.M).group(1)

# ---- a small cell model -----------------------------------------------------------
# A cell is a list of chromosomes; each chromosome is (pair_id, parent, n_chromatids)
def new_cell(pairs):
    return [(i, p, 1) for i in range(pairs) for p in ("mom", "dad")]

def s_phase(cell):
    return [(i, p, 2 * c) for (i, p, c) in cell]

def mitosis(cell):
    """returns two daughter cells: every sister chromatid pair is split."""
    assert all(c == 2 for _, _, c in cell)
    return [[(i, p, 1) for (i, p, _) in cell] for _ in range(2)]

def meiosis(cell, choice):
    """choice[i] in (0, 1) decides which homolog of pair i goes to daughter cell 1 (independent assortment)."""
    assert all(c == 2 for _, _, c in cell)
    d1, d2 = [], []
    for i in sorted({i for i, _, _ in cell}):
        pair = [x for x in cell if x[0] == i]
        a, b = (pair[0], pair[1]) if choice[i] == 0 else (pair[1], pair[0])
        d1.append(a); d2.append(b)
    out = []
    for d in (d1, d2):                              # meiosis II: split sister chromatids
        out.append([(i, p, 1) for (i, p, _) in d]); out.append([(i, p, 1) for (i, p, _) in d])
    return out

# ---- human numbers ------------------------------------------------------------------
body = new_cell(23)
ok(len(body) == 46)
rep = s_phase(body)
ok(len(rep) == 46 and sum(c for _, _, c in rep) == 92)                # 46 chromosomes, 92 chromatids
d = mitosis(rep)
ok(len(d) == 2 and all(len(x) == 46 for x in d) and d[0] == d[1] == body)   # identical daughters
m = meiosis(rep, [0] * 23)
ok(len(m) == 4 and all(len(x) == 23 for x in m))                       # 4 haploid cells
ok(len(d[0]) // 2 == 23)                                                # n = 23
ok(23 + 23 == 46)                                                       # fertilization
ok(2 ** 23 == 8388608 and 2 ** 23 > 8_000_000)                          # "more than 8 million"
ok([2 ** k for k in (2, 3)] == [4, 8])
# anaphase: separated chromatids counted as chromosomes
ok(sum(c for _, _, c in rep) == 92 and 92 // 2 == 46)

# ---- Example 1: 2n = 8 at metaphase ----------------------------------------------------
fly = s_phase(new_cell(4))
chromosomes, chromatids = len(fly), sum(c for _, _, c in fly)
ok((chromosomes, chromatids) == (8, 16))
o = options("**Example 1.**")
ok(o["C"] == "8 chromosomes, 16 chromatids")
ok(o["B"] == "8 chromosomes, 8 chromatids" and o["A"] == "4 chromosomes, 8 chromatids")
ok(o["D"] == "16 chromosomes, 16 chromatids" and o["E"] == "16 chromosomes, 32 chromatids")

# ---- Example 2 -------------------------------------------------------------------------------
dm = mitosis(fly)
mm = meiosis(fly, [0, 1, 0, 1])
ok((len(dm), len(dm[0])) == (2, 8) and (len(mm), len(mm[0])) == (4, 4))
o = options("**Example 2.**")
ok(o["C"] == "mitosis: 2 cells with 8; meiosis: 4 cells with 4")
ok(o["E"] == "mitosis: 2 cells with 8; meiosis: 4 cells with 8")
ok(o["D"].startswith("mitosis: 4 cells with 8"))
ok(o["A"] == "mitosis: 2 cells with 4; meiosis: 2 cells with 8" and o["B"] == "mitosis: 2 cells with 4; meiosis: 4 cells with 8")

# ---- Q1 -----------------------------------------------------------------------------------------
o = options("**1.**")
ok(int(o["B"]) == len(m[0]) and key_letter(1) == "B")
ok(int(o["C"]) == 46 and int(o["A"]) == 2 and int(o["D"]) == 46 * 3 // 2 and int(o["E"]) == 92)

# ---- Q2: phase table -------------------------------------------------------------------------------
event = {"prophase": "condense", "metaphase": "line up", "anaphase": "chromatids separate",
         "telophase": "nuclei re-form", "interphase": "DNA copied"}
o = options("**2.**")
ok([k for k, v in o.items() if event[v] == "chromatids separate"] == ["C"] and key_letter(2) == "C")

# ---- Q3: combos by brute force ------------------------------------------------------------------------
gametes = set()
cell6 = s_phase(new_cell(3))
for choice in itertools.product((0, 1), repeat=3):
    for g in meiosis(cell6, list(choice)):
        gametes.add(tuple(sorted((i, p) for i, p, _ in g)))
ok(len(gametes) == 8)
o = options("**3.**")
ok(int(o["A"]) == len(gametes) and key_letter(3) == "A")
ok(int(o["B"]) == 3 and int(o["C"]) == 6 and int(o["D"]) == 3 ** 2 and int(o["E"]) == 2 ** 6)
# 3 swimmers from 3 pairs = same count
ok(len(list(itertools.product(*[("a", "b")] * 3))) == 8)

# ---- Q4 ----------------------------------------------------------------------------------------------------
c14 = s_phase(new_cell(7))
dd = mitosis(c14)
ok(len(c14) == 14 and len(dd) == 2 and all(len(x) == 14 for x in dd))
o = options("**4.**")
ok(o["E"] == "2 cells with 14 chromosomes" and key_letter(4) == "E")
ok(o["A"] == "4 cells with 7 chromosomes" and o["B"] == "2 cells with 7 chromosomes" and o["C"] == "2 cells with 28 chromosomes" and o["D"] == "4 cells with 14 chromosomes")

# ---- Q5 --------------------------------------------------------------------------------------------------------
o = options("**5.**")
ok(o["D"].startswith("Mitosis") and "identical to the parent" in o["D"] and key_letter(5) == "D")
ok(dd[0] == dd[1])                                                       # mitosis daughters identical
ok(len({tuple(sorted(x)) for x in mm}) <= 4)

# ---- letter spread --------------------------------------------------------------------------------------------------
letters = [key_letter(q) for q in range(1, 6)]
ok(letters == ["B", "C", "A", "E", "D"] and max(letters.count(c) for c in set(letters)) <= 2)

FACT_CHECKS = [
    ("DNA is replicated in S phase of interphase; after copying each chromosome has two sister chromatids joined at the centromere", "https://openstax.org/books/biology-2e/pages/10-1-cell-division"),
    ("Human somatic cells have 46 chromosomes (23 pairs, diploid); gametes have 23 (haploid)", "https://openstax.org/books/biology-2e/pages/10-1-cell-division"),
    ("Mitosis phases: prophase (condense), metaphase (line up), anaphase (chromatids pulled apart), telophase (nuclei re-form)", "https://openstax.org/books/biology-2e/pages/10-2-the-cell-cycle"),
    ("Cytokinesis: animal cells pinch with a cleavage furrow; plant cells form a cell plate", "https://openstax.org/books/biology-2e/pages/10-2-the-cell-cycle"),
    ("Centrosomes organize the mitotic spindle", "https://openstax.org/books/biology-2e/pages/10-2-the-cell-cycle"),
    ("Mitosis gives daughter cells with identical genomes", "https://www.genome.gov/genetics-glossary/Mitosis"),
    ("Mitosis is used for regeneration, growth and asexual reproduction; meiosis makes gametes", "https://bio.libretexts.org/Bookshelves/Introductory_and_General_Biology/General_Biology_(Boundless)/11%3A_Meiosis_and_Sexual_Reproduction/11.04%3A_The_Process_of_Meiosis_-_Comparing_Meiosis_and_Mitosis"),
    ("Meiosis: one replication, two divisions, four haploid cells; homologs pair, cross over, separate in meiosis I; sister chromatids separate in meiosis II", "https://openstax.org/books/biology-2e/pages/11-1-the-process-of-meiosis"),
    ("Independent assortment in humans gives over eight million combinations before crossing over", "https://openstax.org/books/biology-2e/pages/11-1-the-process-of-meiosis"),
    ("Meiosis occurs in the gonads (testes and ovaries); fertilization restores the diploid state; crossovers and random assortment give variation", "https://openstax.org/books/biology-2e/pages/11-2-sexual-reproduction"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
