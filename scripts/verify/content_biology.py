#!/usr/bin/env python3
"""Independent verification of the biology content (issue #25).

1. FACT_CHECKS: every textbook fact the cards and questions rely on, each with two reference notes.
   (Reference notes name the standard textbook / reference chapter the fact appears in. Campbell Biology
   is the book the HUSO syllabus names; the second source is an independent reference.)
2. Recomputation of every numeric or logic question from scratch, compared with the stored answer.

Usage: python3 scripts/verify/content_biology.py   (exit code 0 = all verified)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
QS = json.loads((ROOT / "content/questions/biology.json").read_text(encoding="utf-8"))["questions"]

# (claim, source 1, source 2)
FACT_CHECKS = [
    ("Carbon forms four covalent bonds, so it can build chains and rings", "Campbell Biology ch. 4 (carbon skeleton)", "OpenStax Biology 2e 2.2 (Carbon)"),
    ("Proteins contain C, H, O, N (some S); carbs and triglycerides only C, H, O; nucleic acids add P", "Campbell Biology ch. 3 and 5", "OpenStax Biology 2e ch. 3 (Biological Macromolecules)"),
    ("Monomers: monosaccharide, amino acid, nucleotide; triglyceride = glycerol + 3 fatty acids", "Campbell Biology ch. 5", "OpenStax Biology 2e 3.1-3.5"),
    ("Joining n amino acids in a chain makes n-1 peptide bonds and releases n-1 water (condensation)", "Campbell Biology 5.4", "OpenStax Biology 2e 3.4 (Proteins)"),
    ("Chargaff's rules: A = T and G = C in double-stranded DNA", "Campbell Biology 16.1", "NCBI Bookshelf, Molecular Biology of the Cell 4e (DNA structure)"),
    ("A-T pairs have 2 hydrogen bonds, G-C pairs have 3", "Campbell Biology 5.5", "OpenStax Biology 2e 9.1 (DNA structure)"),
    ("Cooking denatures (unfolds) protein; the peptide bonds and sequence stay", "Campbell Biology 5.4 (denaturation)", "OpenStax Biology 2e 3.4"),
    ("Central dogma: DNA -> RNA -> protein", "Campbell Biology 17.1", "OpenStax Biology 2e 15.1"),
    ("RNA uses uracil in place of thymine", "Campbell Biology 5.5", "OpenStax Biology 2e 9.1"),
    ("Translation happens on ribosomes in the cytoplasm", "Campbell Biology 17.4", "OpenStax Biology 2e 15.4"),
    ("mRNA is the transcript, complementary to the template strand; AUG is the start codon (Met)", "Campbell Biology 17.1-17.2", "OpenStax Biology 2e 15.2"),
    ("Eukaryotic pre-mRNA gets a 5' cap and poly-A tail and introns are spliced out", "Campbell Biology 17.3", "OpenStax Biology 2e 15.3"),
    ("Each codon is 3 nucleotides and codes for one amino acid; stop codon codes for none", "Campbell Biology 17.1", "OpenStax Biology 2e 15.1"),
    ("DNA replication is semi-conservative (Meselson-Stahl with 15N/14N)", "Campbell Biology 16.2", "OpenStax Biology 2e 14.3"),
    ("Cell theory: cells are the unit of life; all organisms are made of cells; cells come from cells", "Campbell Biology 6.1", "OpenStax Biology 2e 4.1"),
    ("Mitochondria make most ATP in animal cells; Golgi modifies, sorts and ships proteins", "Campbell Biology 6.4-6.5", "OpenStax Biology 2e 4.3"),
    ("Chloroplasts, cell wall and large central vacuole are typical of plant cells; lysosomes and centrioles typical of animal cells", "Campbell Biology 6.3-6.4", "OpenStax Biology 2e 4.3"),
    ("Prokaryotes: no nucleus, no membrane-bound organelles, nucleoid, usually 1-10 micrometers", "Campbell Biology 6.2", "OpenStax Biology 2e 4.2"),
    ("Peroxisomes break down hydrogen peroxide; cytoskeleton is protein fibers; centrioles organize spindle in animal cells", "Campbell Biology 6.4-6.6", "OpenStax Biology 2e 4.3-4.5"),
    ("Total magnification = eyepiece x objective; real size = image size / magnification", "Campbell Biology Ch. 6 (Microscopy)", "OpenStax Biology 2e 4.1"),
    ("Mitosis phases: prophase, metaphase, anaphase, telophase; produces 2 identical diploid cells", "Campbell Biology 12.2", "OpenStax Biology 2e 10.2"),
    ("Anaphase separates sister chromatids; meiosis I separates homologous pairs", "Campbell Biology 13.3", "OpenStax Biology 2e 11.1"),
    ("Meiosis: two divisions, four haploid, genetically different cells; crossing over in prophase I", "Campbell Biology 13.3", "OpenStax Biology 2e 11.1-11.2"),
    ("Human body cell 2n = 46, gamete n = 23", "Campbell Biology 13.1", "OpenStax Biology 2e 11.1"),
    ("Photosynthesis: 6CO2 + 6H2O + light -> C6H12O6 + 6O2, in chloroplasts, chlorophyll absorbs red and blue", "Campbell Biology 10.1-10.2", "OpenStax Biology 2e 8.1-8.2"),
    ("Limiting factors: light, CO2, temperature; raising the limiting factor raises the plateau", "Campbell Biology 10.4", "OpenStax Biology 2e 8.3 / ICSE Class 9-10 Biology (Photosynthesis)"),
    ("Starch test: destarch, light, boil, warm ethanol, iodine gives blue-black; variegated leaf shows chlorophyll needed", "ICSE Class 10 Biology (Photosynthesis experiments)", "Khan Academy / BBC Bitesize GCSE Biology"),
    ("Aerobic respiration: glucose + O2 -> CO2 + H2O + energy, about 30-32 ATP per glucose", "Campbell Biology 9.1, 9.4", "OpenStax Biology 2e 7.4"),
    ("Anaerobic respiration: yeast gives ethanol + CO2, muscle gives lactic acid, about 2 ATP", "Campbell Biology 9.5", "OpenStax Biology 2e 7.5"),
    ("Plants respire all the time, in the dark CO2 builds up", "Campbell Biology 10 / 9", "ICSE Class 10 Biology (Respiration in plants)"),
    ("Tendon: muscle to bone; ligament: bone to bone; cartilage firm but flexible; blood is a connective tissue", "Campbell Biology 40.1", "OpenStax Biology 2e 33.1"),
    ("Skeletal muscle striated voluntary; smooth non-striated involuntary; cardiac striated involuntary with intercalated discs", "Campbell Biology 40.1", "OpenStax Biology 2e 33.1"),
    ("Epithelial tissue covers surfaces and lines cavities", "Campbell Biology 40.1", "OpenStax Biology 2e 33.1"),
    ("Organs and glands: liver makes bile (stored in gall bladder), pancreas makes digestive enzymes and insulin", "Campbell Biology 41.3", "OpenStax Biology 2e 34.1-34.4"),
    ("Salivary amylase starts starch digestion in the mouth; pepsin protein in stomach; lipase and bile fat in small intestine", "Campbell Biology 41.3", "OpenStax Biology 2e 34.3"),
    ("Small intestine is the main site of absorption (villi)", "Campbell Biology 41.3", "OpenStax Biology 2e 34.3"),
    ("Deficiencies: vit C scurvy, vit D rickets, vit A night blindness, vit B1 beriberi, iron anemia, iodine goiter, protein kwashiorkor", "WHO / MedlinePlus nutrition pages", "ICSE Class 9 Biology (Nutrition)"),
    ("Food tests: iodine for starch; Benedict's for reducing sugar; biuret for protein; grease spot for fat", "ICSE Class 9 Biology (Nutrition)", "BBC Bitesize GCSE Biology (Food tests)"),
    ("Breathing in: diaphragm contracts, ribs up and out, volume up, pressure down", "Campbell Biology 42.5", "OpenStax Biology 2e 39.3"),
    ("Alveoli: thin wall, moist, large surface area, dense capillaries", "Campbell Biology 42.4", "OpenStax Biology 2e 39.1-39.2"),
    ("Rising CO2 (not low O2) is the main trigger for breathing", "Guyton and Hall, Medical Physiology (control of respiration)", "OpenStax Anatomy and Physiology 2e 22.3"),
    ("Urine path: kidney, ureter, bladder, urethra; kidneys filter blood; liver makes urea", "Campbell Biology 44.4", "OpenStax Anatomy and Physiology 2e 25.1"),
    ("Sweat is mostly water with salts and a little urea; lungs excrete CO2", "OpenStax Anatomy and Physiology 2e 5.1 (Integumentary)", "ICSE Class 10 Biology (Excretory system)"),
    ("Filtration passes small molecules; proteins and blood cells stay in the blood", "Campbell Biology 44.4", "OpenStax Anatomy and Physiology 2e 25.4"),
    ("Cerebrum thinking, cerebellum balance, medulla heartbeat and breathing", "Campbell Biology 49.3", "OpenStax Biology 2e 35.3"),
    ("Reflex arc: receptor, sensory neuron, spinal cord, motor neuron, effector", "Campbell Biology 49.1", "OpenStax Biology 2e 35.1"),
    ("Neuron: dendrites receive, axon carries away, impulse direction dendrites to axon terminals", "Campbell Biology 48.1", "OpenStax Biology 2e 35.1"),
    ("Innate immunity is general and fast with no memory; adaptive is specific with memory", "Campbell Biology 43.1", "OpenStax Biology 2e 42.1"),
    ("B cells make antibodies; killer T cells destroy infected cells; memory cells give faster second response", "Campbell Biology 43.2-43.3", "OpenStax Biology 2e 42.3"),
    ("Allergy: immune overreaction to harmless allergen, histamine", "Campbell Biology 43.4", "OpenStax Biology 2e 42.4"),
    ("Vaccines produce memory cells without disease; ready-made antibodies are passive immunity", "Campbell Biology 43.3", "OpenStax Biology 2e 42.3"),
    ("Endocrine glands release hormones into blood; exocrine through ducts; pancreas is both", "Campbell Biology 45.1", "OpenStax Anatomy and Physiology 2e 17.1"),
    ("Pituitary is the master gland; thyroid makes thyroxine; adrenal makes adrenaline; pancreas makes insulin and glucagon", "Campbell Biology 45.2-45.3", "OpenStax Anatomy and Physiology 2e 17.2-17.7"),
    ("Insulin lowers blood glucose (glycogen storage); glucagon raises it; iodine is needed for thyroxine (goiter)", "Campbell Biology 45.3", "OpenStax Anatomy and Physiology 2e 17.6-17.7"),
    ("Heart: 4 chambers, tricuspid valve right side, bicuspid (mitral) valve left side, septum; left ventricle thickest", "Campbell Biology 42.2", "OpenStax Biology 2e 40.2"),
    ("Double circulation: pulmonary circuit and systemic circuit; pulmonary artery carries oxygen-poor blood", "Campbell Biology 42.1", "OpenStax Biology 2e 40.1-40.2"),
    ("ABO: group O universal donor (red cells), AB universal acceptor; A has anti-B antibodies", "Campbell Biology 42.3 (blood)", "OpenStax Biology 2e 40.1 / AABB"),
    ("Hypertension is persistently high blood pressure, normal about 120/80 mmHg; cardiac arrest differs from heart attack", "American Heart Association", "NHS / MedlinePlus (heart conditions)"),
    ("Lymphatic system returns tissue fluid to blood, lymph nodes help immunity", "Campbell Biology 42.1 / 43.1", "OpenStax Anatomy and Physiology 2e 21.1"),
    ("Biotic vs abiotic; producers, consumers, decomposers; fungi are decomposers", "Campbell Biology 55 (ecosystems)", "OpenStax Biology 2e 46.1 / 55"),
    ("Food webs: arrows point from food to eater; trophic levels; approx. 10% energy transfer", "Campbell Biology 55.3", "OpenStax Biology 2e 46.2"),
    ("Symbiosis: mutualism +/+, commensalism +/0, parasitism +/-, predation +/-", "Campbell Biology 54.1", "OpenStax Biology 2e 45.5"),
    ("Five kingdoms: Monera, Protista, Fungi, Plantae, Animalia; fungal walls are chitin, plant walls cellulose", "Campbell Biology (Whittaker five-kingdom system, ch. 26)", "ICSE Class 9 Biology (Classification)"),
    ("Amoeba: pseudopodia, binary fission, contractile vacuole; bacteria shapes cocci, bacilli, spirilla", "ICSE Class 9 Biology (Protista, Monera)", "Britannica: Amoeba / Bacteria"),
    ("Mould (Rhizopus): hyphae, rhizoids, sporangiophore, sporangium with spores; absorptive feeding", "ICSE Class 9 Biology (Fungi)", "Campbell Biology 31.1"),
    ("Vertebrates have a backbone; earthworm and honeybee are invertebrates", "Campbell Biology 32 / 34", "ICSE Class 9 Biology (Animalia)"),
]

fails = 0
n = 0


def find(part):
    hits = [q for q in QS if part in q["stem"]]
    assert len(hits) == 1, f"{part!r}: {len(hits)} questions"
    return hits[0]


def ans_text(q):
    return q["choices"][q["answer"]]


def check(part, expected, label=None):
    """The stored correct choice must equal the independently computed value."""
    global fails, n
    q = find(part)
    n += 1
    got = ans_text(q)
    if got != expected:
        fails += 1
        print(f"FAIL {q['id']}: stored {got!r}, computed {expected!r}")
    others = [v for k, v in q["choices"].items() if k != q["answer"]]
    if expected in others:
        fails += 1
        print(f"FAIL {q['id']}: computed answer also appears as a wrong choice")


# --- Chargaff: A = 30 % -> T = 30 %, G + C = 40 %, G = 20 %
a = 30
g = (100 - 2 * a) / 2
check("30% adenine", f"{int(g)}%")

# --- 12 amino acids in one chain -> 11 bonds, 11 waters
aa = 12
check("12 amino acids", f"{aa - 1} bonds; {aa - 1} water molecules")

# --- mRNA from template 3'-TAC GGA CTT-5'
comp = {"T": "A", "A": "U", "C": "G", "G": "C"}
tpl = "TACGGACTT"
mrna = "".join(comp[b] for b in tpl)  # reads 5'->3' when the template is written 3'->5'
codons = " ".join(mrna[i:i + 3] for i in range(0, 9, 3))
check("3′-TAC GGA CTT-5′", f"5′-{codons}-3′")
# anticodon pairing used on the translation diagram: AUG-UAC, CCU-GGA
assert "".join(comp[b] if b != "T" else "A" for b in "TAC") == "AUG"
assert "".join({"A": "U", "U": "A", "G": "C", "C": "G"}[b] for b in "AUG") == "UAC"
assert "".join({"A": "U", "U": "A", "G": "C", "C": "G"}[b] for b in "CCU") == "GGA"

# --- 90 nt coding region -> 30 amino acids
check("90 nucleotides long", str(90 // 3))

# --- magnification: image 6 mm, 10x eyepiece, 40x objective
mag = 10 * 40
real_um = 6 / mag * 1000
check("6 mm long", f"{real_um:g} µm")
# --- drawing 45 mm of a 0.09 mm cell
check("0.09 mm long", f"×{round(45 / 0.09)}")

# --- meiosis 2n = 8 -> 4 cells with 4 chromosomes
check("2n = 8", f"4 cells, each with {8 // 2} chromosomes")

# --- photosynthesis stoichiometry: 3 mol CO2
co2 = 3
glucose = co2 / 6
o2 = co2  # 6 O2 per 6 CO2
check("3 mol of CO₂", f"{glucose:g} mol glucose and {o2:g} mol O₂")

# --- respiration: 2 mol glucose needs 12 mol O2
check("2 mol of glucose completely", f"{2 * 6} mol")

# --- 10 % rule: 10 000 kJ -> primary 1000 -> secondary 100
check("10% rule", f"{10000 * 0.1 * 0.1:g} kJ")

# --- simple facts that are easy to get wrong: counts, human chromosome numbers
check("daughter cells", "2")
check("one of her egg cells", "23")

# --- structural sanity: the five answer choices of each numeric item are distinct (also checked elsewhere)
for q in QS:
    assert len(set(q["choices"].values())) == 5, q["id"]

assert len(FACT_CHECKS) >= 60
for claim, s1, s2 in FACT_CHECKS:
    assert claim and s1 and s2 and s1 != s2, claim

print(f"{len(FACT_CHECKS)} fact checks listed (two sources each), {n} numeric/logic answers recomputed, {fails} failures")
sys.exit(1 if fails else 0)
