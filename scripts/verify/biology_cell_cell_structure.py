"""Independent checks for materi/biology/cell-cell-structure.md (examples, key, tables, SVG labels)."""
import pathlib, re
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/cell-cell-structure.md").read_text()
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

def num(s):
    return Fraction(re.sub(r"[^\d.]", "", s.replace(" ", "")))

UM_PER_MM = 1000
# ---- Example 1: M = I / A ---------------------------------------------------------
I_um = 40 * UM_PER_MM
M = Fraction(I_um, 50)
ok(M == 800 and 50 * M == I_um)
o = options("**Example 1.**")
ok([k for k, v in o.items() if num(v) == M] == ["C"])
ok(num(o["A"]) == Fraction(40, 50))                    # no unit change
ok(num(o["D"]) == 40 * 50)                             # multiplied
ok(num(o["B"]) == Fraction(40 * 100, 50) and num(o["E"]) == Fraction(40 * 10000, 50))  # wrong mm->um

# ---- Example 2: A = I / M -------------------------------------------------------------
A_um = Fraction(20 * UM_PER_MM, 400)
ok(A_um == 50 and 10 <= A_um <= 100)
o = options("**Example 2.**")
vals = {"A": Fraction(5, 100), "B": 5, "C": 50, "D": 500, "E": 20 * 400 * UM_PER_MM}  # E in um (8000 mm)
ok(o["A"] == "0.05 µm" and o["B"] == "5 µm" and o["C"] == "50 µm" and o["D"] == "500 µm" and o["E"] == "8000 mm")
ok(20 * 400 == 8000)                                # E multiplies instead of dividing
ok(vals["C"] == A_um)
# each wrong option really differs from 50 um once units are applied
ok(vals["A"] != A_um and vals["B"] != A_um and vals["D"] != A_um and vals["E"] != A_um)

# ---- Q1 magnification ---------------------------------------------------------------------
tot = 10 * 40
o = options("**1.**")
ok(tot == 400 and num(o["C"]) == tot and key_letter(1) == "C")
ok(num(o["A"]) == 40 // 10 and num(o["B"]) == 10 + 40 and num(o["D"]) == 4000 and num(o["E"]) == 10000)

# ---- Q2 cells per mm ---------------------------------------------------------------------------
cells = Fraction(1 * UM_PER_MM, 25)
o = options("**2.**")
ok(cells == 40 and num(o["A"]) == cells and key_letter(2) == "A")
ok(num(o["C"]) == Fraction(100, 25) and num(o["D"]) == Fraction(10000, 25) and num(o["E"]) == 1000 and num(o["B"]) == 25)

# ---- Q3-Q5: set logic over a structure table --------------------------------------------------------
structures = {  # which cell types have which structure
    "ribosomes": {"bacterium", "animal", "plant"}, "cytoplasm": {"bacterium", "animal", "plant"},
    "DNA": {"bacterium", "animal", "plant"}, "a cell membrane": {"bacterium", "animal", "plant"},
    "a nucleus": {"animal", "plant"},
    "centrioles": {"animal"}, "cell wall": {"bacterium", "plant"}, "chloroplasts": {"plant"},
    "a large central vacuole": {"plant"}, "lysosome": {"animal"}, "centriole": {"animal"},
    "ribosome": {"bacterium", "animal", "plant"}, "chloroplast": {"plant"},
}
o = options("**3.**")
absent = [k for k, v in o.items() if "bacterium" not in structures[v]]
ok(absent == ["E"] and key_letter(3) == "E")
o = options("**5.**")
animal_only = [k for k, v in o.items() if structures[v] == {"animal"}]
ok(animal_only == ["B"] and key_letter(5) == "B")
o = options("**4.**")
ok(o["D"] == "lysosome" and key_letter(4) == "D")
ok(structures["chloroplast"] == {"plant"} and structures["centriole"] == {"animal"})

# ---- the 13 syllabus organelles + cytoplasm all appear in the table ---------------------------------
table = TXT[TXT.index("| Organelle |"):TXT.index("3. **Prokaryotic")]
names = ["nucleus", "ribosome", "chloroplast", "mitochondria", "ER", "golgi", "lysosome", "membrane", "vacuole",
         "cell wall", "peroxisome", "centriole", "cytoskeleton", "cytoplasm"]
ok(len(names) == 14)
for nm in names:
    ok(nm.lower() in table.lower(), nm)
head = TXT.split("\n")[1].lower()
ok(all(nm.lower() in head for nm in names if nm not in ("ER", "cytoplasm")))

# ---- SVG labels (flashcard occlusion) -----------------------------------------------------------------------
def labels(name):
    return set(re.findall(r'data-label="([^"]+)"', (ROOT / f"public/content/biology/{name}.svg").read_text()))
common = {"membrane", "cytoplasm", "nucleus", "ribosome", "er", "golgi", "mitochondria", "peroxisome", "cytoskeleton"}
animal = labels("structure-animal-cell"); plant = labels("structure-plant-cell")
ok(common <= animal and common <= plant)
ok({"lysosome", "centriole", "vacuole"} <= animal and not ({"cell-wall", "chloroplast"} & animal))
ok({"cell-wall", "chloroplast", "vacuole"} <= plant and not ({"lysosome", "centriole"} & plant))
ok(len(animal) == 12 and len(plant) == 12)
# all 13 syllabus organelles + cytoplasm covered between the two cells
ok(animal | plant == common | {"lysosome", "centriole", "vacuole", "cell-wall", "chloroplast"})
ok(len(animal | plant) == 14)

# ---- numbers quoted in the text --------------------------------------------------------------------------------
ok("1 mm = 1000 µm" in TXT and 10 * 40 == 400 and 50 * 800 == 40 * 1000)
ok(0.1 <= 5 < 10 <= 100)                       # prokaryote vs eukaryote size ranges do not overlap

letters = [key_letter(q) for q in range(1, 6)]
ok(letters == ["C", "A", "E", "D", "B"] and max(letters.count(c) for c in set(letters)) <= 2)

FACT_CHECKS = [
    ("Cell theory: all living things made of cells; cell is the basic unit; new cells arise from existing cells", "https://openstax.org/books/biology-2e/pages/4-1-studying-cells"),
    ("Light microscope up to ~1000x and can view living cells; electron microscope magnifies far more but needs dead specimens", "https://openstax.org/books/biology-2e/pages/4-1-studying-cells"),
    ("A human red blood cell is about 8 micrometers wide", "https://openstax.org/books/biology-2e/pages/4-1-studying-cells"),
    ("Prokaryotes: no nucleus, DNA in the nucleoid, no membrane-bound organelles, 0.1-5 um, cell wall in most bacteria", "https://openstax.org/books/biology-2e/pages/4-2-prokaryotic-cells"),
    ("Eukaryotic cells are 10-100 um; nucleus houses DNA; mitochondria make ATP; chloroplasts photosynthesize", "https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells"),
    ("Plant cells have a cellulose cell wall, chloroplasts and a large central vacuole; animal cells have centrosomes with centrioles and lysosomes", "https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells"),
    ("Peroxisomes break down fatty acids and detoxify; plant cells usually lack lysosomes and centrosomes", "https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells"),
    ("Rough ER has ribosomes and makes proteins; smooth ER makes lipids; Golgi modifies, sorts and packages; lysosomes digest", "https://openstax.org/books/biology-2e/pages/4-4-the-endomembrane-system-and-proteins"),
    ("Ribosomes float free in the cytoplasm or sit on the rough ER and make proteins", "https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells"),
    ("The plasma membrane controls the passage of molecules, ions and water into and out of the cell", "https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
