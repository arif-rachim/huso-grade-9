#!/usr/bin/env python3
"""Lint learning material: python3 scripts/check_materi.py [--links] [materi/math/*.md ...]

Checks every subtopic file (and README / lembar-ringkas for relative links):
  * template sections exist in order (English headings), header slug is a real subtopic of content/syllabus.json
  * 1-3 video/simulation links, 5 "Check your understanding" questions (1.-5.) with options (A)..(E), a key in <details>
  * relative links and images exist; every SVG is well formed with a viewBox, no <script>/external href
  * --links : also verifies http(s) links are alive (YouTube via oEmbed, others HTTP 200)
Exit code 1 if anything fails.
"""
import json, re, subprocess, sys, pathlib, xml.dom.minidom, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SECTIONS = ["## 🖼️ Big picture", "## 💡 Core ideas", "## 🧮 HUSO-style examples", "## ⚠️ Common traps",
            "## ✏️ Redraw from memory", "## 🎥 Watch / try", "## ✅ Check your understanding (5 questions)"]
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36"}
syl = json.load(open(ROOT / "content/syllabus.json"))
SLUGS = {c["slug"] for s in syl["subjects"] for t in s["topics"] for c in t["children"]}
errors = []
def err(f, m): errors.append(f"{f}: {m}")

def check_svg(path, shown):
    try:
        d = xml.dom.minidom.parse(str(path))
    except Exception as e:
        return err(shown, f"SVG not well formed: {e}")
    root = d.documentElement
    if not root.getAttribute("viewBox"): err(shown, "SVG without viewBox")
    raw = path.read_text()
    if re.search(r"<script|<foreignObject|<image|xlink:href|\shref=\"https?:|javascript:", raw, re.I):
        err(shown, "SVG has script/foreignObject/image/external href")
    if re.search(r'<svg[^>]*\s(width|height)="\d+(px)?"', raw): err(shown, "SVG must not have fixed width/height")

def check_url(u):
    try:
        if "youtube.com/watch" in u or "youtu.be/" in u:
            j = json.loads(urllib.request.urlopen(urllib.request.Request(
                "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(u, safe=""), headers=UA), timeout=25).read())
            return True, f"{j['author_name']} | {j['title']}"
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25)
        return r.status == 200, f"HTTP {r.status}"
    except Exception as e:
        return False, str(e)

def check_file(p, links):
    shown = str(p.relative_to(ROOT))
    t = p.read_text()
    # relative links / images
    for m in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)\)", t):
        u = m.group(1)
        if u.startswith(("http://", "https://", "#", "mailto:")): continue
        target = (p.parent / u.split("#")[0]).resolve()
        if not target.exists(): err(shown, f"broken relative link: {u}")
        elif target.suffix == ".svg": check_svg(target, str(target.relative_to(ROOT)))
    if p.name in ("README.md", "lembar-ringkas.md"): return
    first = t.splitlines()[0]
    m = re.search(r"`([a-z\-]+\.[a-z\-]+\.[a-z\-]+)`\s*$", first)
    if not first.startswith("# ") or not m: return err(shown, "first line must be '# {emoji} {Name}  ·  `{slug}`'")
    if m.group(1) not in SLUGS: err(shown, f"unknown subtopic slug {m.group(1)}")
    if not re.search(r"^> 📅 Study date: .*⏱️ ~12 min read · 📋 Syllabus: ", t, re.M): err(shown, "missing '> 📅 Study date … 📋 Syllabus' line")
    pos = -1
    for s in SECTIONS:
        i = t.find(s)
        if i < 0: err(shown, f"missing section '{s}'")
        elif i < pos: err(shown, f"section out of order '{s}'")
        else: pos = i
    if not re.search(r"!\[[^\]]+\]\(\.\./\.\./public/content/[a-z]+/[^)]+\.svg\)", t): err(shown, "no SVG image '![alt](../../public/content/...svg)'")
    # hook before first template section
    head = t[:t.find(SECTIONS[0])] if SECTIONS[0] in t else ""
    if not re.search(r"🍳|🎮|🏊", head): err(shown, "hook before '🖼️ Big picture' must use a 🍳/🎮/🏊 theme (docs/STUDENT.md)")
    # videos
    vs = t[t.find(SECTIONS[5]):t.find(SECTIONS[6])] if SECTIONS[5] in t and SECTIONS[6] in t else ""
    urls = re.findall(r"\]\((https?://[^)\s]+)\)", vs)
    if not 1 <= len(urls) <= 3: err(shown, f"'Watch / try' needs 1-3 links, found {len(urls)}")
    for line in vs.splitlines():
        if line.startswith("- ") and not re.search(r"—.*·", line): err(shown, f"video line needs '— channel · length · what to watch for': {line[:60]}")
    # check-your-understanding block
    cp = t[t.find(SECTIONS[6]):]
    qs = re.findall(r"^\*\*(\d)\.\*\*", cp.split("<details>")[0], re.M)
    if qs != ["1", "2", "3", "4", "5"]: err(shown, f"'Check your understanding' must have questions 1.-5., found {qs}")
    for q in range(1, 6):
        blk = re.search(rf"^\*\*{q}\.\*\*(.*?)(?=^\*\*{q+1}\.\*\*|<details>)", cp, re.S | re.M)
        if not blk or not all(f"({c})" in blk.group(1) for c in "ABCDE"): err(shown, f"question {q}: needs options (A)..(E)")
    if "<details><summary>Answer key & explanations</summary>" not in cp or "</details>" not in cp: err(shown, "missing <details> key block")
    else:
        key = cp.split("<details>")[1]
        for q in range(1, 6):
            if not re.search(rf"^{q}\. \*\*\(([A-E])\)", key, re.M): err(shown, f"key {q}: expected '{q}. **(X) ...'")
    if links:
        for u in urls:
            ok, info = check_url(u)
            print(("OK   " if ok else "FAIL ") + u + " | " + info)
            if not ok: err(shown, f"dead link {u}")
    for line in t.splitlines():
        if line.startswith("- [") and "](http" in line and links is False: pass

def main(argv):
    links = "--links" in argv
    files = [pathlib.Path(a).resolve() for a in argv if not a.startswith("--")]
    if not files: files = sorted((ROOT / "materi").rglob("*.md"))
    for f in files: check_file(f, links)
    for svg in sorted((ROOT / "public/content").rglob("*.svg")): check_svg(svg, str(svg.relative_to(ROOT)))
    if errors:
        print("\n".join(errors)); print(f"\n{len(errors)} problem(s)"); sys.exit(1)
    print(f"OK: {len(files)} markdown file(s) checked")

main(sys.argv[1:])
