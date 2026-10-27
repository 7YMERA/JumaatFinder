# JumaatFinder

A web app that locates where you can solat Jumaat easily. You might travel far
not knowing one is just beside you or very near you! It doesn't have to be a
full-fledged mosque to do the weekly prayer — many surau in KL hold Jumaat too.
Built first for busy places like Mid Valley KL, where it's hard to know where to
go and when to leave.

## What it does
- **Countdown** to this Friday's Zuhr / azan Jumaat (JAKIM times via
  [waktusolat.app](https://waktusolat.app), auto zone from GPS, falls back to WLY01).
- **Nearby masjid and surau** within 3 km from OpenStreetMap, sorted by distance,
  with walking time. Masjid count as holding Jumaat; surau show as
  *unconfirmed* until you mark them ✅ *Has Jumaat* or ❌ *No Jumaat*.
- **"Leave by" time** for each mosque, using walk time plus a buffer you choose,
  with an *On track / Leave now / Too late on foot* status.
- **Directions** in Google Maps or Waze, and a **weekly Friday reminder** (.ics)
  for your calendar.
- **Personal notes** per mosque (e.g. "full by 1:05pm, overflow at car park L2"),
  saved on your phone.
- Works without GPS: pick Mid Valley, The Gardens, Bangsar South, KL Sentral or KLCC.

## Run it
The app is plain static files, with no build step:

```bash
python3 -m http.server 8000   # open http://localhost:8000
```

Without a backend, marks, notes and pin fixes stay on your phone only.

## Deploy on Vercel (with shared reports)
1. On [vercel.com](https://vercel.com), **Add New → Project**, import
   `7YMERA/JumaatFinder`, leave every setting as default, **Deploy**.
   The site goes live at `https://<project>.vercel.app` (HTTPS, so GPS works).
2. In the project: **Storage → Create Database → Neon (Postgres)**, free plan,
   connect it to the project. This adds `DATABASE_URL` automatically.
3. **Deployments → Redeploy**. The `reports` table is created on first use.

With the database connected, everyone shares:
- ✅/❌ "Has Jumaat" votes (one per person per place; surau with more ✅ than ❌
  show as confirmed for everyone),
- 📣 crowd reports ("hall full by 1:05pm"), shown for 35 days,
- 📍 pin fixes (a listed surau moves once two people agree).

`api/reports.js` validates input, keeps people's IPs only as salted hashes,
and limits each person to 20 reports an hour. Optionally set `IP_SALT` to a
random string in the project's environment variables.

## Official data
`data/surau_jumaat_selangor.json` holds the **113 surau approved for Solat Jumaat**
listed on the [JAIS e-Masjid](https://e-masjid.jais.gov.my/dashboard/listsuraujumaat)
portal (Petaling, Hulu Langat, Hulu Selangor, Gombak, Klang), geocoded with
OpenStreetMap Nominatim. `precision` says how each pin was found: `poi` (the
surau itself), `street`, or `postcode` (approximate; shown with ≈ in the app).
JAIS's portal does not list all of the state's approved surau, so a missing
surau may still hold Jumaat.

Refresh it:

```bash
python3 scripts/scrape_jais.py > data/surau_jumaat_selangor.raw.json
python3 scripts/geocode.py data/surau_jumaat_selangor.raw.json data/surau_jumaat_selangor.json
python3 scripts/build_official.py data/surau_jumaat_*.json > data/official.js
```

KL (JAWI) is not included yet.

## Adding data
Edit `data.js`: `JUMAAT_PRESETS` holds the "pick a place" starting points, and
`JUMAAT_SEED` holds hand-checked places that always show, merged with OpenStreetMap.
Add `jumaat: true` to a surau there once it's confirmed, so it shows as
confirmed for everyone.

## Ideas for next steps
- Shared "has Jumaat" marks and crowd reports ("hall full at 1:02pm"), so
  everyone sees them, not just you.
- Verified khutbah start times and capacity per place.
