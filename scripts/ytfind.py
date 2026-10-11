#!/usr/bin/env python3
"""Find and verify YouTube videos for learning material (no API key needed).

  ytfind.py search "vieta formulas"      -> top results: id | channel | length | title
  ytfind.py check URL [URL ...]          -> verifies each URL is alive (oEmbed) and prints title + channel

Used by agents writing materi/*.md: every video link must pass `check` and its title must be
about the subtopic. Prefer channels listed in docs/CONTENT.md / the Materi issues.
"""
import json, re, sys, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf8", "replace")

def search(q, n=8):
    html = get("https://www.youtube.com/results?search_query=" + urllib.parse.quote(q) + "&hl=en")
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if not m:
        print("no results parsed"); return
    data = json.loads(m.group(1))
    out = []
    def walk(o):
        if isinstance(o, dict):
            if "videoRenderer" in o:
                v = o["videoRenderer"]
                vid = v["videoId"]
                title = "".join(r.get("text", "") for r in v["title"]["runs"])
                ch = "".join(r.get("text", "") for r in v.get("ownerText", {}).get("runs", []))
                ln = v.get("lengthText", {}).get("simpleText", "?")
                out.append((vid, ch, ln, title))
            for x in o.values(): walk(x)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(data)
    for vid, ch, ln, title in out[:n]:
        print(f"https://www.youtube.com/watch?v={vid} | {ch} | {ln} | {title}")

def check(urls):
    bad = 0
    for u in urls:
        try:
            if "youtube.com" in u or "youtu.be" in u:
                j = json.loads(get("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(u, safe="")))
                print(f"OK   {u} | {j['author_name']} | {j['title']}")
            else:
                req = urllib.request.Request(u, headers=UA)
                r = urllib.request.urlopen(req, timeout=25)
                t = re.search(r"<title[^>]*>(.*?)</title>", r.read(200000).decode("utf8", "replace"), re.S | re.I)
                print(f"OK   {u} | HTTP {r.status} | {(t.group(1).strip() if t else '')[:90]}")
        except Exception as e:
            bad += 1; print(f"FAIL {u} | {e}")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "search": search(" ".join(sys.argv[2:]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "check": check(sys.argv[2:])
    else: print(__doc__)
