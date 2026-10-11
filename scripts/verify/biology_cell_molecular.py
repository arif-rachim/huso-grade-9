"""Independent checks for materi/biology/cell-molecular.md (examples + check questions)."""
import itertools, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/cell-molecular.md").read_text()
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

# ---- molecular helpers --------------------------------------------------------
DNA_TO_RNA = {"A": "U", "T": "A", "G": "C", "C": "G"}
DNA_PAIR = {"A": "T", "T": "A", "G": "C", "C": "G"}
CODON_TABLE = {"AUG": "Met", "UUC": "Phe", "UUU": "Phe", "GGA": "Gly", "GGC": "Gly", "GCU": "Ala",
               "CCU": "Pro", "AAG": "Lys", "UAA": "stop", "UAG": "stop", "UGA": "stop"}

def transcribe(template_3to5):
    """Template written 3'->5'; mRNA comes out 5'->3' aligned letter by letter."""
    return "".join(DNA_TO_RNA[b] for b in template_3to5)

def translate(mrna_5to3):
    i = mrna_5to3.find("AUG")
    if i < 0: return None
    chain = []
    for j in range(i, len(mrna_5to3) - 2, 3):
        aa = CODON_TABLE[mrna_5to3[j:j + 3]]
        if aa == "stop": break
        chain.append(aa)
    return "-".join(chain)

# count of codons: 4^3, 61 + 3
ok(4 ** 3 == 64 and 64 - 3 == 61 and len(["UAA", "UAG", "UGA"]) == 3)
# 3-letter stop codons really are the only ones among the three listed in the table
ok(sorted(c for c, a in CODON_TABLE.items() if a == "stop") == ["UAA", "UAG", "UGA"])

# ---- Example 1 ---------------------------------------------------------------
m1 = transcribe("TACGGATTCATT")
ok(m1 == "AUGCCUAAGUAA")
o = options("**Example 1.**")
ok(o["A"] == "5′-AUGCCUAAGUAA-3′")
ok(o["B"] == "5′-" + m1.replace("U", "T") + "-3′")                     # T instead of U
ok(o["C"] == "5′-UACGGAUUCAUU-3′" and o["C"][3:-3] == "TACGGATTCATT".replace("T", "U"))  # template copied with U
ok(o["D"][3:-3] == m1[::-1] and o["D"] == "5′-AAUGAAUCCGUA-3′")         # reversed
ok(o["E"] == "5′-TACGGATTCATT-3′")
ok([m1[i:i + 3] for i in range(0, 12, 3)] == ["AUG", "CCU", "AAG", "UAA"])
ok(translate(m1) == "Met-Pro-Lys" and len(translate(m1).split("-")) == 3)

# ---- Example 2 ---------------------------------------------------------------
card = "GCAUGUUCGGAGCUUAAGC"
ok(card.find("AUG") == 2)
ok(translate(card) == "Met-Phe-Gly-Ala")
ok([card[i:i + 3] for i in range(2, 17, 3)] == ["AUG", "UUC", "GGA", "GCU", "UAA"] and card[17:] == "GC")
o = options("**Example 2.**")
ok(o["A"] == "Met–Phe–Gly–Ala" and o["B"] == "Met–Phe–Gly" and o["C"] == "Phe–Gly–Ala")
ok(o["E"].startswith("No protein"))
# reading from the first letter would not give Met first (trap logic of E)
ok(card[:3] != "AUG")

# ---- Q1 -----------------------------------------------------------------------
m = transcribe("TTAGCC")
ok(m == "AAUCGG")
o = options("**1.**")
ok(o["A"] == f"5′-{m}-3′" and key_letter(1) == "A")
ok(o["B"] == f"5′-{m.replace('U','T')}-3′")
ok(o["C"] == "5′-UUAGCC-3′" and "TTAGCC".replace("T", "U") == "UUAGCC")
ok(o["D"] == f"5′-{m[::-1]}-3′" and m[::-1] == "GGCUAA")
ok(o["E"] == f"5′-{m[::-1].replace('U','T')}-3′")

# ---- Q2 hydrogen bonds ---------------------------------------------------------
HB = {"A": 2, "T": 2, "G": 3, "C": 3}
at, gc = 4, 6
total = at * 2 + gc * 3
ok(at + gc == 10 and total == 26)
o = options("**2.**")
ok(int(o["C"]) == total and key_letter(2) == "C")
ok(int(o["A"]) == 10 * 2 and int(o["B"]) == at * 3 + gc * 2 and int(o["D"]) == 10 * 3 and int(o["E"]) == 2 * total)
# strand-level recount: 20 bases, one strand has 4 A/T-bases and 6 G/C-bases
strand = "AATTGGGCCC"
partner = "".join(DNA_PAIR[b] for b in strand)
ok(sum(HB[b] for b in strand) == total and len(partner) == 10)

# ---- Q3 introns ----------------------------------------------------------------
pre, introns = 300, [60, 90]
left = pre - sum(introns)
ok(left == 150 and left % 3 == 0)
aa = left // 3 - 1                      # last codon is stop
ok(aa == 49)
o = options("**3.**")
ok(int(o["D"]) == aa and key_letter(3) == "D")
ok(int(o["A"]) == left // 3 and int(o["C"]) == pre // 3 and int(o["E"]) == pre // 3 - 1)
ok(int(o["B"]) == (pre - 90) // 3 and (pre - 90) % 3 == 0)
ok(50 + 60 + 40 == 150 and 50 + 60 + 90 + 60 + 40 == 300)   # numbers in the RNA-processing figure

# ---- Q4 --------------------------------------------------------------------------
o = options("**4.**")
ok(o["B"] == "transcription" and key_letter(4) == "B")

# ---- Q5 semiconservative simulation ------------------------------------------------
def replicate(mol):
    a, b = mol            # two strands, each labeled 15 or 14 (old strand keeps its label)
    return [(a, 14), (b, 14)]
pop = [(15, 15)]
for _ in range(2):
    pop = [m2 for m in pop for m2 in replicate(m)]
ok(len(pop) == 4)
heavy = sum(1 for m in pop if 15 in m)
ok(heavy == 2 and sum(1 for m in pop if m == (14, 14)) == 2)
o = options("**5.**")
ok(int(o["C"]) == heavy and key_letter(5) == "C")
ok([int(o[k]) for k in "ABCDE"] == [4, 3, 2, 1, 0])

# ---- spread + structure ---------------------------------------------------------------
letters = [key_letter(q) for q in range(1, 6)]
ok(letters == ["A", "C", "D", "B", "C"] and max(letters.count(c) for c in set(letters)) <= 2)
for q in range(1, 6):
    ok(re.search(rf"^\*\*{q}\.\*\*", TXT, re.M) is not None)

FACT_CHECKS = [
    ("DNA: double helix, sugar-phosphate backbone outside, A-T two hydrogen bonds, G-C three, strands antiparallel", "https://openstax.org/books/biology-2e/pages/14-2-dna-structure-and-sequencing"),
    ("Replication is semiconservative: each daughter DNA keeps one parental strand (Meselson-Stahl)", "https://openstax.org/books/biology-2e/pages/14-3-basics-of-dna-replication"),
    ("Helicase unwinds the helix; DNA polymerase adds nucleotides 5' to 3'", "https://openstax.org/books/biology-2e/pages/14-4-dna-replication-in-prokaryotes"),
    ("RNA polymerase transcribes in the nucleus, synthesizing pre-mRNA 5' to 3'", "https://openstax.org/books/biology-2e/pages/15-3-eukaryotic-transcription"),
    ("RNA has uracil instead of thymine and ribose instead of deoxyribose, and is usually single-stranded", "https://openstax.org/books/biology-2e/pages/3-5-nucleic-acids"),
    ("Pre-mRNA gets a 5' cap, a poly-A tail, and introns are spliced out in the nucleus", "https://openstax.org/books/biology-2e/pages/15-4-rna-processing-in-eukaryotes"),
    ("64 codons: 61 specify amino acids, 3 are stop codons; AUG is start (Met); code is degenerate", "https://openstax.org/books/biology-2e/pages/15-1-the-genetic-code"),
    ("Stop codons are UAA, UAG, UGA; initiator tRNA carries methionine; anticodon pairs with codon", "https://openstax.org/books/biology-2e/pages/15-5-ribosomes-and-protein-synthesis"),
    ("Peptide bonds join amino acids, releasing water; ribosome moves three nucleotides along the mRNA", "https://openstax.org/books/biology-2e/pages/15-5-ribosomes-and-protein-synthesis"),
    ("tRNAs carry specific amino acids; ribosome has a small subunit binding mRNA and a large subunit binding tRNA", "https://openstax.org/books/biology-2e/pages/15-5-ribosomes-and-protein-synthesis"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
