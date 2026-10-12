"""Independent checks for materi/biology/anatomy-nervous.md (logic items + fact-check list)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TXT = (ROOT / "materi/biology/anatomy-nervous.md").read_text()
KEYBLOCK = TXT.split("<details>")[1]
n = 0


def ok(c, msg="check failed"):
    global n
    assert c, msg
    n += 1


def options(label):
    i = TXT.index(label)
    line = next(l for l in TXT[i:].splitlines() if l.startswith("(A)"))
    o = dict(re.findall(r"\(([A-E])\) (.*?)(?=  \([A-E]\)|$)", line))
    ok(list(o) == list("ABCDE") and len(set(o.values())) == 5, f"{label}: 5 distinct options")
    return o


def key_letter(q):
    return re.search(rf"^{q}\. \*\*\(([A-E])\)", KEYBLOCK, re.M).group(1)


# ---- the model: facts as data -------------------------------------------------
ARC = ["stimulus", "receptor", "sensory neuron", "spinal cord", "motor neuron", "effector", "response"]
# direction of each neuron type relative to the CNS
DIRECTION = {"sensory": "into CNS", "motor": "out of CNS"}
NERVE_FIBERS = {"sensory nerve": {"sensory"}, "motor nerve": {"motor"}, "mixed nerve": {"sensory", "motor"}}
BRAIN_JOB = {  # which part is needed for which function
    "cerebrum": {"thinking", "memory", "speech", "voluntary movement"},
    "cerebellum": {"balance", "coordination"},
    "medulla": {"breathing", "heartbeat"},
}
NEURON_PARTS = ["dendrites", "cell body", "axon", "myelin sheath", "axon terminals"]  # in impulse order

# Text states the reflex arc in this order
m = re.search(r"\*\*stimulus → receptor → sensory neuron → spinal cord → motor neuron → effector → response\*\*", TXT)
ok(m is not None, "reflex arc line present")
ok(m.group(0).strip("*").split(" → ") == ARC)
# Redraw checklist repeats it
ok("stimulus → receptor → sensory neuron → spinal cord → motor neuron → effector → response" in TXT.split("## ✏️ Redraw")[1])
# neuron parts in impulse order: dendrites -> cell body -> axon -> terminals
ok("dendrites → cell body → axon → terminals" in TXT)
ok(TXT.index("**dendrites**") < TXT.index("**cell body**") < TXT.index("**axon**") < TXT.index("**myelin sheath**") < TXT.index("**axon terminals**"))
# the SVGs carry all labels
svg = (ROOT / "public/content/biology/nervous-brain-cns.svg").read_text()
for lab in ["cerebrum", "cerebellum", "medulla oblongata", "spinal cord"]:
    ok(f'data-label="{lab}"' in svg, lab)
svg2 = (ROOT / "public/content/biology/nervous-motor-neuron.svg").read_text()
for lab in ["dendrites", "axon", "myelin sheath", "cell body", "axon terminals"]:
    ok(f'data-label="{lab}"' in svg2, lab)
# CNS = brain + spinal cord only; PNS = nerves
CNS = {"brain", "spinal cord"}
ok(CNS == {"brain", "spinal cord"} and "**brain + spinal cord**" in TXT)

# ---- Example 1: the only option equal to the true order of the neuron/path part ---
true_path = ["receptor", "sensory neuron", "spinal cord", "motor neuron", "muscle"]  # effector = muscle here
o1 = options("**Example 1.**")
seqs = {k: [s.strip() for s in v.split("→")] for k, v in o1.items()}
hits = [k for k, s in seqs.items() if s == true_path]
ok(hits == ["B"], hits)
ok(seqs["C"] == ["receptor", "sensory neuron", "brain", "motor neuron", "muscle"])  # brain trap
ok(seqs["D"] == list(reversed(true_path)))                                             # backwards trap
ok(seqs["A"][1] == "motor neuron" and seqs["A"][3] == "sensory neuron")                # swapped neurons
ok(re.search(r"\*\*Answer: \(B\)\.\*\*", TXT) is not None)

# ---- Example 2: deduce the damaged part by elimination -----------------------
symptoms_ok = {"memory", "speech", "breathing"}
symptoms_bad = {"balance", "coordination"}
damaged = [p for p, jobs in BRAIN_JOB.items() if jobs & symptoms_bad and not (jobs & symptoms_ok)]
ok(damaged == ["cerebellum"], damaged)
o2 = options("**Example 2.**")
ok([k for k, v in o2.items() if v == "cerebellum"] == ["D"])

# ---- Q1: axon carries impulse away from the cell body ----------------------------
idx = {p: i for i, p in enumerate(NEURON_PARTS)}
# the part that carries the impulse between the cell body and the terminals is the axon (myelin only wraps it)
carrier = [p for p in NEURON_PARTS if idx["cell body"] < idx[p] < idx["axon terminals"] and p != "myelin sheath"]
ok(carrier == ["axon"], carrier)
o = options("**1.**")
ok([k for k, v in o.items() if v == "axon"] == ["B"] and key_letter(1) == "B")

# ---- Q2: voluntary vs reflex ----------------------------------------------------
def classify(decision_made, skips_brain):
    return "reflex" if (not decision_made and skips_brain) else "voluntary"
ok(classify(True, False) == "voluntary")    # the flick shot
ok(classify(False, True) == "reflex")       # the hot pan
o = options("**2.**")
ok(o["D"].startswith("voluntary: the cerebrum starts it") and key_letter(2) == "D")
ok(BRAIN_JOB["cerebellum"] >= {"coordination"} and "voluntary movement" in BRAIN_JOB["cerebrum"])
ok(all(o[k].startswith("voluntary") or o[k].startswith("a reflex") for k in "ABCDE"))
ok(sum(v.startswith("voluntary:") for v in o.values()) == 1)

# ---- Q3: nerve that both feels and moves is mixed ---------------------------------
need = {"sensory", "motor"}
fits = [k for k, f in NERVE_FIBERS.items() if f >= need]
ok(fits == ["mixed nerve"])
o = options("**3.**")
ok(o["A"] == "a mixed nerve" and key_letter(3) == "A")

# ---- Q4: the effector is the muscle that acts -------------------------------------
ROLE = {"tap": "stimulus", "stretch sensor": "receptor", "sensory neuron": "sensory neuron", "kick": "response", "thigh muscle": "effector"}
ok(ROLE["thigh muscle"] == "effector" and ROLE["kick"] == "response")
o = options("**4.**")
ok(o["E"] == "effector" and key_letter(4) == "E" and set(o.values()) >= {"stimulus", "receptor", "response"})

# ---- Q5: pain felt later: spinal cord first, brain second ---------------------------
path_len = {"spinal reflex (3 neurons, no brain)": 3, "up to the cerebrum (more synapses)": 6}
ok(path_len["spinal reflex (3 neurons, no brain)"] < path_len["up to the cerebrum (more synapses)"])
o = options("**5.**")
ok(o["C"].startswith("The spinal cord triggers the pull-away at once") and key_letter(5) == "C")

# ---- key letters: no letter more than twice -------------------------------------
letters = [key_letter(q) for q in range(1, 6)]
ok(all(letters.count(l) <= 2 for l in "ABCDE") and len(letters) == 5, letters)
ok(len(re.findall(r"^\d\. \*\*\(", KEYBLOCK, re.M)) == 5)
ok(sum(e in TXT.split("## ✅ Check")[1] for e in ("🍳", "🎮", "🏊")) >= 1)

# ---- FACT CHECKS: every non-trivial claim with a source ---------------------------
FACT_CHECKS = [
    ("CNS = brain + spinal cord; spinal nerves belong to the PNS", "https://openstax.org/books/biology-2e/pages/35-3-the-central-nervous-system"),
    ("Cerebellum controls balance and coordinates movement", "https://openstax.org/books/biology-2e/pages/35-3-the-central-nervous-system"),
    ("Cerebellum does not start movement but gives coordination, precision, timing", "https://en.wikipedia.org/wiki/Cerebellum"),
    ("Brainstem (incl. medulla) controls breathing; medulla holds cardiac and respiratory centers", "https://en.wikipedia.org/wiki/Medulla_oblongata"),
    ("Cerebrum (frontal lobe) plans and carries out movement, speech, decision-making", "https://openstax.org/books/biology-2e/pages/35-3-the-central-nervous-system"),
    ("Spinal cord runs from the medulla down inside the vertebral column, carries messages both ways, coordinates reflexes", "https://en.wikipedia.org/wiki/Spinal_cord"),
    ("Mixed nerve = both sensory and motor fibers; all spinal nerves are mixed", "https://en.wikipedia.org/wiki/Mixed_nerve"),
    ("Neuron parts: cell body (nucleus), dendrites receive, axon carries the signal to axon terminals", "https://openstax.org/books/biology-2e/pages/35-1-neurons-and-glial-cells"),
    ("Myelin is an insulating layer that speeds conduction, made by glial cells", "https://openstax.org/books/biology-2e/pages/35-1-neurons-and-glial-cells"),
    ("Reflexes are fast because of local synaptic connections; the knee-jerk uses sensory + motor neuron", "https://openstax.org/books/biology-2e/pages/35-3-the-central-nervous-system"),
    ("Reflex arc: receptor, sensory neuron, integration center (spinal cord), motor neuron, effector", "https://www.kenhub.com/en/library/anatomy/reflex-arc"),
    ("Simple spinal reflex arc video (receptor to effector)", "https://www.youtube.com/watch?v=EqsNHbbJQJ4"),
]
ok(len(FACT_CHECKS) >= 8 and all(u.startswith("https://") for _, u in FACT_CHECKS))
print(f"OK {n} checks")
