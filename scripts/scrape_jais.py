"""Scrape JAIS e-Masjid surau approved for Solat Jumaat (Selangor) into JSON.

Combines the "Senarai Surau Solat Jumaat" page with the general surau list,
where a few approved surau only carry a "(Jumaat)" marker in their name.

Usage: python3 scripts/scrape_jais.py > data/surau_jumaat_selangor.raw.json
"""
import html
import json
import re
import sys
import urllib.request

URL = "https://e-masjid.jais.gov.my/dashboard/listsuraujumaat"
SURAU_URL = "https://e-masjid.jais.gov.my/dashboard/listsurau"
UA = "JumaatFinder/0.1 (https://github.com/7YMERA/JumaatFinder)"
DISTRICTS = {"petaling": "Petaling", "gombak": "Gombak", "klang": "Klang", "klgt": "Kuala Langat",
             "spg": "Sepang", "hlgt": "Hulu Langat", "ksel": "Kuala Selangor", "hsel": "Hulu Selangor",
             "sbk": "Sabak Bernam"}
ADDRESS_START = (r"No\.?|Lot|Jalan|Jln\.?|Kg\.?|Kampung|Tmn\.?|Taman|Persiaran|Blok|Pangsapuri|Lorong|Lrg\.?"
                 r"|Bt\.?|Batu|Seksyen|Sek\.?|Bandar|Kompleks|Apartment|Pusat")


def clean(cell):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", cell)).split())


def split_name(raw):
    """'SURAU X (SURAU SOLAT JUMAAT) address 40150' -> ('Surau X', 'address 40150')."""
    m = re.match(r"(.*?)\s*[\(,]*\s*\(?\s*(?:surau\s+)?(?:kebenaran\s+|institusi\s+)?(?:solat\s+)?jumaat\s*\)?[,\s]*(.*)", raw, re.I)
    name, addr = (m.group(1).strip(" ,("), m.group(2).strip()) if m else (raw, "")
    # Marker missing or placed after the address: cut the name at the first address-looking word.
    cut = re.search(rf"[,\s]+(?=(?:{ADDRESS_START})\b)", name, re.I)
    marker_after_address = len(addr) < 15  # only a postcode/town left after the marker
    if cut and marker_after_address and len(name[:cut.start()].split()) >= 2:
        name, addr = name[:cut.start()], (name[cut.end():] + " " + addr).strip()
    return name.title(), addr.title()


def parse(page, url=URL, jumaat_only=False):
    out = []
    for m in re.finditer(r'id="surau-(\w+)"', page):  # tab panes only, not "...-tab" buttons
        t0 = page.find("<table", m.end())
        table = page[t0:page.find("</table>", t0)]
        for row in re.findall(r"<tr.*?</tr>", table, re.S):
            cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            if len(cells) < 5 or (jumaat_only and not re.search(r"jumaat", cells[1], re.I)):
                continue
            name, addr = split_name(cells[1])
            pc = re.search(r"\b(\d{5})\s*$", cells[1])
            out.append({"name": name, "address": addr, "postcode": pc.group(1) if pc else None,
                        "district": DISTRICTS.get(m.group(1), m.group(1)), "state": "Selangor",
                        "kariah": cells[3].title(), "status": "surau_jumaat",
                        "source": "JAIS", "source_url": url})
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace")


if __name__ == "__main__":
    rows = parse(fetch(URL))
    seen = {(r["name"].lower(), r["postcode"]) for r in rows}
    rows += [r for r in parse(fetch(SURAU_URL), SURAU_URL, jumaat_only=True)
             if (r["name"].lower(), r["postcode"]) not in seen]
    json.dump(rows, sys.stdout, ensure_ascii=False, indent=1)
