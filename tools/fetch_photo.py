#!/usr/bin/env python3
"""Find and download a free-to-use photo from Wikimedia Commons.

Usage: python3 fetch_photo.py "<search terms>" <out_dir>
Writes <out_dir>/photo.jpg and <out_dir>/photo.json (author, licence, source URL, credit line).
Only accepts public domain, CC0, CC BY and CC BY-SA. Exits 2 if nothing usable or the network blocks it,
in which case draw an SVG background instead (see CLAUDE.md).
"""
import json, re, sys, urllib.parse, urllib.request

API = "https://commons.wikimedia.org/w/api.php"
OK = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? ?\d(\.\d)?)", re.I)
UA = {"User-Agent": "exploreaustralianbeauty-story-bot/1.0 (instagram content; contact via owner)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()

def strip(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()

def main(q, out):
    params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} filetype:bitmap",
              "gsrnamespace": 6, "gsrlimit": 30, "prop": "imageinfo", "iiprop": "url|size|extmetadata",
              "iiurlwidth": 2000}
    try:
        data = json.loads(get(API + "?" + urllib.parse.urlencode(params)))
    except Exception as e:
        print(f"network error: {e}", file=sys.stderr); sys.exit(2)
    best = None
    for p in (data.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = strip(md.get("LicenseShortName", {}).get("value", ""))
        if not OK.match(lic) or ii.get("width", 0) < 1200:
            continue
        score = ii["width"] * ii["height"] * (1.5 if ii["height"] >= ii["width"] else 1)  # prefer portrait for 9:16
        if not best or score > best[0]:
            best = (score, p["title"], ii, lic, md)
    if not best:
        print("no free-licence photo found", file=sys.stderr); sys.exit(2)
    _, title, ii, lic, md = best
    author = strip(md.get("Artist", {}).get("value", "")) or "Unknown"
    with open(f"{out}/photo.jpg", "wb") as f:
        f.write(get(ii.get("thumburl") or ii["url"]))
    meta = {"title": title, "author": author, "licence": lic, "source": ii["descriptionurl"],
            "credit": f"Photo: {author} / {lic} / Wikimedia Commons"}
    json.dump(meta, open(f"{out}/photo.json", "w"), indent=2)
    print(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
