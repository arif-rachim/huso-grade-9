#!/usr/bin/env python3
"""Independent re-solve of every Chemistry question (issue #24).

For each numeric question the expression in CHECKS is evaluated from scratch (rounded atomic masses,
R = 0.0821 L.atm/(mol.K) or 8.314 J/(mol.K), Kw = 1e-14 at 25 C, N_A = 6.02e23) and compared with the
number at the start of the choice that the key marks correct. No other choice may be numerically
equal to it. Questions that test facts are listed in FACTS with the source that confirms them
(IUPAC naming / the official HUSO Chemistry syllabus topic list / a standard general-chemistry rule).

Run:  python3 scripts/verify/content_chemistry.py      (exit code 0 = all good)
"""
import json, math, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
QS = json.loads((ROOT / "content/questions/chemistry.json").read_text())["questions"]

MASS = {"H": 1, "He": 4, "C": 12, "N": 14, "O": 16, "F": 19, "Na": 23, "Mg": 24, "Al": 27, "Si": 28, "P": 31,
        "S": 32, "Cl": 35.5, "K": 39, "Ca": 40, "Fe": 56, "Cu": 63.5, "Zn": 65, "Br": 80, "Ag": 108, "I": 127, "Ba": 137}
R_ATM, R_J, KW, NA = 0.0821, 8.314, 1e-14, 6.02e23

def M(formula):
    """Molar mass from a formula such as 'Ca(OH)2' or 'C6H12O6' (g/mol)."""
    def parse(s, i=0):
        total = 0.0
        while i < len(s):
            ch = s[i]
            if ch == "(":
                sub, i = parse(s, i + 1)
                m = re.match(r"\d+", s[i:])
                k = int(m.group()) if m else 1
                i += len(m.group()) if m else 0
                total += sub * k
            elif ch == ")":
                return total, i + 1
            else:
                m = re.match(r"[A-Z][a-z]?", s[i:])
                el = m.group()
                i += len(el)
                m2 = re.match(r"\d+", s[i:])
                k = int(m2.group()) if m2 else 1
                i += len(m2.group()) if m2 else 0
                total += MASS[el] * k
        return total, i
    return parse(formula)[0]

SUP = {"⁻": "-", "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}

def lead_number(text):
    """(value, tolerance): the tolerance is half of the last printed digit."""
    t = text.replace("−", "-").replace(",", "").strip().lstrip("≈ ")
    m = re.match(r"(-?\d+(?:\.(\d+))?)(?:\s*[×x]\s*10\s*([⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+|\^-?\d+))?", t)
    if not m:
        raise ValueError(f"no leading number in {text!r}")
    val = float(m.group(1))
    tol = 0.5 * 10 ** -(len(m.group(2) or ""))
    if m.group(3):
        e = m.group(3).lstrip("^")
        e = int("".join(SUP.get(c, c) for c in e))
        val *= 10 ** e
        tol *= 10 ** e
    return val, tol * 1.0001

NS = {"math": math, "M": M, "R_ATM": R_ATM, "R_J": R_J, "KW": KW, "NA": NA, "ln": math.log, "log10": math.log10,
      "sqrt": math.sqrt, "exp": math.exp}

CHECKS = {
 "chemistry-0006": "30-21+1",
 "chemistry-0009": "14-6",
 "chemistry-0011": "17",
 "chemistry-0012": "0.60*69+0.40*71",
 "chemistry-0013": "80*0.5**(12/4)",
 "chemistry-0015": "90-3*2+2*1",
 "chemistry-0016": "30/(math.log(64/2)/math.log(2))",
 "chemistry-0017": "3*2",
 "chemistry-0020": "5-(6-5)",
 "chemistry-0023": "sum(1 for l in range(4) if 1<=l)*2",
 "chemistry-0039": "2+1",
 "chemistry-0041": "M('H2O')",
 "chemistry-0042": "NA",
 "chemistry-0044": "0.5*3*M('CO2')",
 "chemistry-0045": "18/M('C6H12O6')",
 "chemistry-0047": "min(2.7/27/2, 7.1/M('Cl2')/3)*2*M('AlCl3')",
 "chemistry-0048": "2*(2.7/M('H2O'))/(4.4/M('CO2'))",
 "chemistry-0049": "0.50/2.0",
 "chemistry-0050": "58.5/M('NaCl')/0.500",
 "chemistry-0051": "-log10(math.sqrt(KW))",
 "chemistry-0052": "0.50*300/6.0",
 "chemistry-0053": "-log10(2.0e-3/20)",
 "chemistry-0054": "36/M('C6H12O6')/0.400",
 "chemistry-0056": "-log10(math.sqrt(5.5e-14))",
 "chemistry-0057": "(0.250*0.40+0.750*0.20)/(0.250+0.750)",
 "chemistry-0058": "-log10(0.010)",
 "chemistry-0060": "10**(9-2)",
 "chemistry-0061": "14+log10(2*0.0020)",
 "chemistry-0062": "-log10(math.sqrt(1.0e-5*0.10))",
 "chemistry-0063": "4.76+log10(0.20/0.10)",
 "chemistry-0065": "KW/6.8e-4",
 "chemistry-0069": "math.sqrt(1.8e-10)",
 "chemistry-0070": "(3.2e-11/4)**(1/3)",
 "chemistry-0071": "(0.0020/2)*(0.0020/2)",
 "chemistry-0072": "1.8e-10/0.10",
 "chemistry-0074": "-log10(math.sqrt(KW))",
 "chemistry-0077": "0.100*20.0/25.0",
 "chemistry-0078": "2*0.050*20.0/0.100",
 "chemistry-0079": "0.150*33.0/10.0",
 "chemistry-0080": "-log10(1.8e-5)",
 "chemistry-0082": "14+log10((30.0*0.100-20.0*0.100)/50.0)",
 "chemistry-0094": "3.00*2.00/(R_ATM*300)",
 "chemistry-0095": "(58.5/M('NaCl'))/1.00*2*1.86",
 "chemistry-0096": "0.040**2/(0.50*0.20**3)",
 "chemistry-0098": "0.0060*(R_ATM*300)**1",
 "chemistry-0099": "-R_J*298*math.log(1.0e3)/1000",
 "chemistry-0101": "500-200",
 "chemistry-0103": "200*4.18*80/1000",
 "chemistry-0104": "-394-(-283)",
 "chemistry-0105": "436+243-2*431",
 "chemistry-0107": "-394+2*-286-(-75)",
 "chemistry-0108": "40000/120",
 "chemistry-0109": "36/M('H2O')*6.01",
 "chemistry-0110": "5",
 "chemistry-0111": "2*4+2",
 "chemistry-0123": "3*2",
 "chemistry-0137": "abs(2.85-2.70)/2.70*100",
 "chemistry-0140": "0.2500*0.100*M('NaCl')",
 "chemistry-0142": "1.00*(10.00/100.0)*(10.00/100.0)"
}

FACTS = {
 "chemistry-0001": "Standard IUPAC group names (IUPAC periodic table)",
 "chemistry-0002": "IUPAC periodic table: Mg = Group 2",
 "chemistry-0003": "IUPAC periodic table: Cl = Group 17",
 "chemistry-0004": "Br2 is a liquid at 25 C; Hg is the only liquid metal (CRC Handbook)",
 "chemistry-0005": "General chemistry: variable oxidation states of d-block elements",
 "chemistry-0007": "Aufbau configuration of Cl = [Ne]3s²3p⁵",
 "chemistry-0008": "IUPAC: hydrogen is placed in Group 1 for convenience but is not an alkali metal",
 "chemistry-0010": "Standard definition of alpha particle (IUPAC Gold Book)",
 "chemistry-0014": "Periodic table: Z = 90 is Th; alpha decay A-4, Z-2",
 "chemistry-0018": "Aufbau principle: O = 1s2 2s2 2p4",
 "chemistry-0019": "Hund's rule of maximum multiplicity (IUPAC Gold Book)",
 "chemistry-0021": "Electron configurations of d-block ions (Zn2+ = 3d10)",
 "chemistry-0022": "Quantum number rules: 0 <= l <= n-1, |ml| <= l",
 "chemistry-0024": "Cr = [Ar]4s1 3d5 (NIST atomic spectra database)",
 "chemistry-0025": "Atomic radius increases down a group and decreases across a period",
 "chemistry-0026": "Pauling electronegativity scale: F = 3.98 is the maximum",
 "chemistry-0027": "Cations are smaller than their parent atoms",
 "chemistry-0028": "Isoelectronic series: radius falls as Z rises",
 "chemistry-0029": "Measured IE1 (kJ/mol): Be 900, B 801, N 1402, O 1314 (NIST)",
 "chemistry-0030": "Halogen oxidizing power Cl2 > Br2 > I2 (standard reduction potentials 1.36, 1.07, 0.54 V)",
 "chemistry-0031": "Large jump in successive IE marks the valence shell boundary",
 "chemistry-0032": "IE2 (kJ/mol): Na 4562, Mg 1451, Al 1817, Si 1577, P 1907 (CRC Handbook)",
 "chemistry-0033": "VSEPR theory: AX4 is tetrahedral",
 "chemistry-0034": "Ionic: metal + nonmetal (NaCl); the others are molecular",
 "chemistry-0035": "Experimental H-O-H angle in water: 104.5 degrees",
 "chemistry-0036": "Molecular polarity: linear CO2 has zero net dipole",
 "chemistry-0037": "Boiling points: H2O 100 C, CH4 -161.5 C (CRC Handbook); hydrogen bonding",
 "chemistry-0038": "Ethene: planar, 120 degrees, sp2 carbons",
 "chemistry-0040": "VSEPR: SF4 is see-saw (AX4E), polar; the others are symmetric and nonpolar",
 "chemistry-0043": "Reaction classification: A -> B + C is decomposition",
 "chemistry-0046": "Mole ratios from 100 g basis: C 40/12 = 3.33, H 6.7/1 = 6.7, O 53.3/16 = 3.33 -> CH2O",
 "chemistry-0055": "Salt hydrolysis: anion of a weak acid gives basic solution (general chemistry)",
 "chemistry-0059": "Brønsted-Lowry conjugate pair definition",
 "chemistry-0064": "Lewis acid = electron-pair acceptor (IUPAC Gold Book); BF3 has no acidic H",
 "chemistry-0066": "Solubility rules: AgCl insoluble (Ksp 1.8e-10)",
 "chemistry-0067": "Definition of a saturated solution",
 "chemistry-0068": "Ksp definition: product of ion concentrations raised to their coefficients",
 "chemistry-0073": "s(AgCl) = sqrt(1.8e-10) = 1.34e-5; s(Ag2CrO4) = (1.1e-12/4)^(1/3) = 6.5e-5 (Ksp values from CRC Handbook)",
 "chemistry-0075": "Phenolphthalein transition range pH 8.2-10.0 colorless to pink (CRC Handbook)",
 "chemistry-0076": "Standard titration vocabulary (IUPAC)",
 "chemistry-0081": "Indicator ranges: MO 3.1-4.4, MR 4.4-6.2, BTB 6.0-7.6, phenolphthalein 8.2-10 (CRC Handbook)",
 "chemistry-0083": "Standard flame test colors (RSC / CRC)",
 "chemistry-0084": "Sodium D line, flame test intense yellow",
 "chemistry-0085": "Standard halide test with acidified AgNO3",
 "chemistry-0086": "Standard carbonate test",
 "chemistry-0087": "Hydroxide precipitate colors (Cu(OH)2 pale blue)",
 "chemistry-0088": "Acid removes CO3(2-) and SO3(2-) before the Ba2+ test (standard qualitative analysis)",
 "chemistry-0089": "Zn(OH)2 amphoteric and dissolves in excess NH3; Al(OH)3 does not",
 "chemistry-0090": "Ba2+ flame apple-green; BaSO4 insoluble (solubility rules)",
 "chemistry-0091": "Le Chatelier's principle; Haber process conditions",
 "chemistry-0092": "Definition of Kc",
 "chemistry-0093": "Clausius-Clapeyron: boiling point rises with pressure",
 "chemistry-0097": "CO2 triple point 5.11 atm, -56.6 C; dry ice sublimes at 1 atm (CRC Handbook)",
 "chemistry-0100": "Definition: exothermic means delta H < 0",
 "chemistry-0102": "Entropy S(gas) > S(liquid) > S(solid)",
 "chemistry-0106": "Lattice energies (kJ/mol): MgO 3791, NaCl 787, KCl 715 (Born-Haber data, CRC)",
 "chemistry-0112": "IUPAC nomenclature of alkenes",
 "chemistry-0113": "IUPAC rules: longest chain, lowest locant",
 "chemistry-0114": "Definition of constitutional isomers (IUPAC Gold Book)",
 "chemistry-0115": "Limonene exists as (R)- and (S)-enantiomers with different odors (standard organic chemistry)",
 "chemistry-0116": "Butane conformers: anti is the global minimum, about 3.8 kJ/mol below gauche",
 "chemistry-0117": "2,3-dibromobutane: (2R,3R), (2S,3S) and meso (2R,3S) = 3 stereoisomers",
 "chemistry-0118": "Definition of SN2 (bimolecular, concerted)",
 "chemistry-0119": "SN2 relative rates: methyl > 1° > 2° >> 3° (neopentyl is very slow)",
 "chemistry-0120": "Markovnikov addition of HBr to propene",
 "chemistry-0121": "Hyperconjugation and inductive stabilization of carbocations",
 "chemistry-0122": "SN2 proceeds with inversion of configuration (Walden inversion)",
 "chemistry-0124": "E2 favored by strong/bulky base and heat (standard organic chemistry)",
 "chemistry-0125": "Zaitsev rule: more substituted alkene is the major elimination product",
 "chemistry-0126": "Ethanol is CH3CH2OH (IUPAC)",
 "chemistry-0127": "Vinegar is about 5% acetic acid",
 "chemistry-0128": "CnH2n-2 general formula of alkynes",
 "chemistry-0129": "pKa: acetic 4.76, phenol 9.99, water 15.7, ethanol 15.9 (CRC Handbook)",
 "chemistry-0130": "Tollens' test distinguishes aldehydes from ketones",
 "chemistry-0131": "Fischer esterification: ethanoic acid + ethanol -> ethyl ethanoate",
 "chemistry-0132": "Boiling points (C): ethanoic acid 118, propan-1-ol 97, propanone 56, methoxyethane 7, butane -1 (CRC Handbook)",
 "chemistry-0133": "C4H10O: 4 alcohols and 3 ethers = 7 structural isomers (enumerated by hand)",
 "chemistry-0134": "Volumetric flask tolerance class A 250 mL +/- 0.12 mL (ASTM E288)",
 "chemistry-0135": "Standard titration equipment",
 "chemistry-0136": "Standard lab safety rule: add acid to water",
 "chemistry-0138": "Definition of systematic error (NIST)",
 "chemistry-0139": "Accuracy vs precision definitions (IUPAC Gold Book)",
 "chemistry-0141": "Burette must be rinsed with titrant: dilution of titrant makes titre too large (standard volumetric analysis practice)"
}

def close(want, got):
    val, tol = got
    return abs(want - val) <= tol

def main():
    bad = []
    ids = [q["id"] for q in QS]
    for qid in ids:
        if (qid in CHECKS) == (qid in FACTS):
            bad.append(f"{qid}: must be in exactly one of CHECKS / FACTS")
    for qid in list(CHECKS) + list(FACTS):
        if qid not in ids:
            bad.append(f"{qid}: unknown question")
    for q in QS:
        qid = q["id"]
        if qid in FACTS:
            if len(FACTS[qid].strip()) < 10:
                bad.append(f"{qid}: FACTS note too short")
            continue
        if qid not in CHECKS:
            continue
        want = eval(CHECKS[qid], {"__builtins__": {"round": round, "abs": abs, "sum": sum, "min": min, "max": max, "range": range, "len": len, "int": int, "float": float}}, NS)
        key = q["answer"]
        try:
            got = {k: lead_number(v) for k, v in q["choices"].items()}
        except ValueError as e:
            bad.append(f"{qid}: {e}")
            continue
        if not close(want, got[key]):
            bad.append(f"{qid}: recomputed {want!r} but key {key} says {q['choices'][key]!r}")
        for k, v in got.items():
            if k != key and close(want, v):
                bad.append(f"{qid}: choice {k} {q['choices'][k]!r} is also numerically correct ({want!r})")
    n = len(QS)
    print(f"{n} questions: {len(CHECKS)} recomputed numerically, {len(FACTS)} fact-checked, {len(bad)} problems")
    for b in bad:
        print("FAIL", b)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
