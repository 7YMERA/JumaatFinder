"""Geocode surau entries with Nominatim (1 req/s, identified User-Agent).

Usage: python3 scripts/geocode.py in.json out.json
Tries the surau's name, then its street, then its postcode, and records which one
matched in "precision". A name/street hit that lands far from the entry's own
postcode area is treated as a namesake elsewhere and replaced by the postcode.
Results are cached in out.json.cache so re-runs are fast.
"""
import json, math, re, sys, time, urllib.parse, urllib.request
UA = "JumaatFinder/0.1 (https://github.com/7YMERA/JumaatFinder)"
cache_path = sys.argv[2] + ".cache"
try: cache = json.load(open(cache_path))
except Exception: cache = {}
def q(text):
    if text in cache: return cache[text]
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": text, "format": "jsonv2", "limit": 5, "countrycodes": "my"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                res = json.load(r); break
        except Exception as e:
            print("retry", text, e, file=sys.stderr); time.sleep(5)
    else: res = []
    time.sleep(1.1)
    hit = None
    for h in res:
        # Bus stops are often named after the masjid ("Masjid X (Opp)"): skip them.
        if h.get("category") in ("highway", "public_transport", "railway") or "(Opp)" in h.get("display_name", ""):
            continue
        lat, lon = float(h["lat"]), float(h["lon"])
        if 2.4 < lat < 3.95 and 100.7 < lon < 102.1:  # Selangor / KL / Putrajaya
            hit = {"lat": round(lat, 6), "lng": round(lon, 6), "match": h.get("display_name", "")}
            break
    cache[text] = hit
    json.dump(cache, open(cache_path, "w"))
    return hit
def km(a, b):
    rad = math.pi / 180
    h = math.sin((b["lat"] - a["lat"]) * rad / 2) ** 2 + math.cos(a["lat"] * rad) * math.cos(b["lat"] * rad) * math.sin((b["lng"] - a["lng"]) * rad / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))
items = json.load(open(sys.argv[1]))
for i, it in enumerate(items):
    region = it.get("state") or "Malaysia"
    pc = it.get("postcode") or ""
    street = re.search(r"((?:Jalan|Jln\.?|Lorong|Persiaran)\s[^,]+?)(?=,|\s\d{5}|$)", it["address"], re.I)
    tries = [(f"{it['name']}, {pc}, {region}", "poi")]
    # JAIS names often carry extras OSM doesn't ("Masjid Kariah X, Seri Kembangan").
    short = re.sub(r"\b(kariah|jamek|kampung|kg\.?)\b", " ", it["name"].split(",")[0], flags=re.I)
    short = " ".join(re.sub(r"\bsek(?:syen)?\.?\s*\w+$", "", short, flags=re.I).split())
    for variant in dict.fromkeys([it["name"].split(",")[0].strip(), short]):
        if it.get("district"):
            tries.append((f"{variant}, {it['district']}, {region}", "poi"))
    if street: tries.append((f"{street.group(1).replace('Jln.', 'Jalan').replace('Jln', 'Jalan')}, {pc}, {region}", "street"))
    if pc: tries.append((f"{pc}, {region}, Malaysia", "postcode"))
    it["lat"] = it["lng"] = None; it["precision"] = None
    pc_hit = q(f"{pc}, {region}, Malaysia") if pc else None
    for text, prec in tries:
        hit = q(text)
        if hit and prec != "postcode" and pc_hit and pc not in hit["match"] and km(hit, pc_hit) > 4:
            continue  # namesake in another area
        if hit:
            it.update(lat=hit["lat"], lng=hit["lng"], precision=prec, geocode_match=hit["match"]); break
    print(i + 1, len(items), it["precision"], it["name"], file=sys.stderr)
json.dump(items, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
