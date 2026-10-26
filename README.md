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
It is plain static files, with no build step and no backend:

```bash
python3 -m http.server 8000   # open http://localhost:8000
```

Deploy the folder to any static host (Vercel, Netlify, GitHub Pages).
GPS needs HTTPS (or localhost).

## Adding data
Edit `data.js`: `JUMAAT_PRESETS` holds the "pick a place" starting points, and
`JUMAAT_SEED` holds hand-checked places that always show, merged with OpenStreetMap.
Add `jumaat: true` to a surau there once it's confirmed, so it shows as
confirmed for everyone.

## Ideas for next steps
- Shared "has Jumaat" marks and crowd reports ("hall full at 1:02pm"), so
  everyone sees them, not just you.
- Verified khutbah start times and capacity per place.
