"""Scrape every Selangor masjid from JAIS e-Masjid (list + profile pages).

Usage: python3 scripts/scrape_jais_masjid.py > data/masjid_selangor.raw.json
Keeps the masjid's own details (name, address, district, category, capacity);
committee members' names and phone numbers are not collected.
"""
import html
import json
import re
import sys
import time
import urllib.request

BASE = "https://e-masjid.jais.gov.my"
UA = "JumaatFinder/0.1 (https://github.com/7YMERA/JumaatFinder)"


def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print("retry", path, e, file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    return ""


def text(page):
    return " ".join(html.unescape(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", page, flags=re.S)).split())


def field(txt, label, nxt):
    m = re.search(rf"{label}\s+(.*?)\s+(?:{nxt})\b", txt)
    return m.group(1).strip() if m else None


def main():
    listing = get("/dashboard/listmasjid")
    rows = re.findall(r"<tr>\s*<td>\d+</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>.*?/profail/masjid/(\d+)/showhome", listing, re.S)
    out = []
    for i, (name, district, category, mid) in enumerate(rows):
        txt = text(get(f"/profail/masjid/{mid}/showhome"))
        addr = field(txt, "Alamat", "Daerah")
        cap = field(txt, "Kapasiti", "Keluasan")
        cap_n = re.sub(r"[^\d]", "", cap or "")
        pc = re.search(r"\b(\d{5})\b", addr or "")
        out.append({"name": html.unescape(name).strip().title(), "address": (addr or "").title(),
                    "postcode": pc.group(1) if pc else None, "district": district.strip(), "state": "Selangor",
                    "category": category.strip(), "capacity": int(cap_n) if cap_n and int(cap_n) < 100000 else None,
                    "status": "masjid", "source": "JAIS",
                    "source_url": f"{BASE}/profail/masjid/{mid}/showhome"})
        print(i + 1, len(rows), out[-1]["name"], out[-1]["capacity"], file=sys.stderr)
        time.sleep(1)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
