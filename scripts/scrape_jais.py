"""Scrape JAIS e-Masjid "Senarai Surau Solat Jumaat" (Selangor) into JSON.

Usage: python3 scripts/scrape_jais.py > data/surau_jumaat_selangor.raw.json
"""
import html
import json
import re
import sys
import urllib.request

URL = "https://e-masjid.jais.gov.my/dashboard/listsuraujumaat"
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
    m = re.match(r"(.*?)\s*[\(,]*\s*\(?\s*(?:surau\s+)?(?:kebenaran\s+)?solat\s+jumaat\s*\)?[,\s]*(.*)", raw, re.I)
    name, addr = (m.group(1).strip(" ,("), m.group(2).strip()) if m else (raw, "")
    if not addr:
        # No "(Solat Jumaat)" marker: cut the name at the first address-looking word.
        cut = re.search(rf"[,\s]+(?=(?:{ADDRESS_START})\b)", name, re.I)
        if cut:
            name, addr = name[:cut.start()], name[cut.end():]
    return name.title(), addr.title()


def parse(page):
    out = []
    for m in re.finditer(r'id="surau-([\w-]+)"', page):
        t0 = page.find("<table", m.end())
        table = page[t0:page.find("</table>", t0)]
        for row in re.findall(r"<tr.*?</tr>", table, re.S):
            cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            if len(cells) < 5:
                continue
            name, addr = split_name(cells[1])
            pc = re.search(r"\b(\d{5})\s*$", cells[1])
            out.append({"name": name, "address": addr, "postcode": pc.group(1) if pc else None,
                        "district": DISTRICTS.get(m.group(1), m.group(1)), "state": "Selangor",
                        "kariah": cells[3].title(), "status": "surau_jumaat",
                        "source": "JAIS", "source_url": URL})
    return out


if __name__ == "__main__":
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        page = r.read().decode("utf-8", "replace")
    json.dump(parse(page), sys.stdout, ensure_ascii=False, indent=1)
