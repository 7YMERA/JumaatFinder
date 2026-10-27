// Shared reports so one person's finding helps everyone:
//   jumaat_yes / jumaat_no  — "this surau does / doesn't hold Jumaat"
//   crowd                   — short note, e.g. "hall full at 1:05pm"
//   pin                     — "it's actually here" location fix
//
// GET  /api/reports?lat=..&lng=..   aggregates for places within ~4 km
// POST /api/reports {key, name, lat, lng, type, note?, pinLat?, pinLng?}
//
// Needs DATABASE_URL (Postgres, e.g. Neon via Vercel → Storage). The table is
// created on first use.
import { neon } from "@neondatabase/serverless";
import { createHash } from "node:crypto";

const TYPES = new Set(["jumaat_yes", "jumaat_no", "crowd", "pin"]);
const MAX_PER_HOUR = 20;
const NEAR_DEG = 0.04; // ~4.4 km box around the viewer

let ready;
function db() {
  if (!process.env.DATABASE_URL) return null;
  const sql = neon(process.env.DATABASE_URL);
  ready ??= sql`
    CREATE TABLE IF NOT EXISTS reports (
      id         bigserial PRIMARY KEY,
      place_key  text NOT NULL,
      place_name text NOT NULL,
      lat        double precision NOT NULL,
      lng        double precision NOT NULL,
      type       text NOT NULL,
      note       text,
      pin_lat    double precision,
      pin_lng    double precision,
      ip_hash    text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now()
    )`.then(() => sql`CREATE INDEX IF NOT EXISTS reports_geo ON reports (lat, lng)`);
  return sql;
}

const num = (v) => (Number.isFinite(+v) ? +v : NaN);
const inMalaysia = (lat, lng) => lat > 0.8 && lat < 7.5 && lng > 99.5 && lng < 119.5;

function ipHash(req) {
  const ip = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim() || "unknown";
  return createHash("sha256").update(ip + (process.env.IP_SALT || "jumaat")).digest("hex").slice(0, 16);
}

export default async function handler(req, res) {
  const sql = db();
  if (!sql) return res.status(503).json({ error: "shared reports not configured" });
  await ready;

  if (req.method === "GET") {
    const lat = num(req.query.lat), lng = num(req.query.lng);
    if (!inMalaysia(lat, lng)) return res.status(400).json({ error: "bad location" });
    const rows = await sql`
      SELECT place_key,
             count(*) FILTER (WHERE type = 'jumaat_yes')::int AS yes,
             count(*) FILTER (WHERE type = 'jumaat_no')::int  AS no,
             count(*) FILTER (WHERE type = 'pin')::int        AS pins,
             avg(pin_lat) FILTER (WHERE type = 'pin')          AS pin_lat,
             avg(pin_lng) FILTER (WHERE type = 'pin')          AS pin_lng,
             (array_agg(json_build_object('note', note, 'at', created_at) ORDER BY created_at DESC)
                FILTER (WHERE type = 'crowd' AND created_at > now() - interval '35 days'))[1:3] AS crowd
        FROM reports
       WHERE lat BETWEEN ${lat - NEAR_DEG} AND ${lat + NEAR_DEG}
         AND lng BETWEEN ${lng - NEAR_DEG} AND ${lng + NEAR_DEG}
       GROUP BY place_key`;
    res.setHeader("Cache-Control", "s-maxage=30, stale-while-revalidate=60");
    return res.status(200).json({ places: rows });
  }

  if (req.method === "POST") {
    const b = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
    const lat = num(b.lat), lng = num(b.lng);
    const key = String(b.key || "").slice(0, 120);
    const name = String(b.name || "").slice(0, 120);
    const note = b.type === "crowd" ? String(b.note || "").trim().slice(0, 140) : null;
    const pinLat = b.type === "pin" ? num(b.pinLat) : null;
    const pinLng = b.type === "pin" ? num(b.pinLng) : null;
    if (!TYPES.has(b.type) || !key || !name || !inMalaysia(lat, lng)) return res.status(400).json({ error: "bad report" });
    if (b.type === "crowd" && !note) return res.status(400).json({ error: "empty note" });
    if (b.type === "pin" && (!inMalaysia(pinLat, pinLng) || Math.abs(pinLat - lat) > 0.05 || Math.abs(pinLng - lng) > 0.05)) {
      return res.status(400).json({ error: "pin too far from the listed place" });
    }
    const who = ipHash(req);
    const [{ n }] = await sql`SELECT count(*)::int AS n FROM reports WHERE ip_hash = ${who} AND created_at > now() - interval '1 hour'`;
    if (n >= MAX_PER_HOUR) return res.status(429).json({ error: "too many reports, try later" });
    // One yes/no vote per person per place: replace their earlier vote.
    if (b.type === "jumaat_yes" || b.type === "jumaat_no") {
      await sql`DELETE FROM reports WHERE place_key = ${key} AND ip_hash = ${who} AND type IN ('jumaat_yes', 'jumaat_no')`;
    }
    await sql`INSERT INTO reports (place_key, place_name, lat, lng, type, note, pin_lat, pin_lng, ip_hash)
              VALUES (${key}, ${name}, ${lat}, ${lng}, ${b.type}, ${note}, ${pinLat}, ${pinLng}, ${who})`;
    return res.status(201).json({ ok: true });
  }

  res.setHeader("Allow", "GET, POST");
  return res.status(405).json({ error: "method not allowed" });
}
