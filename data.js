// Starting points users can pick without GPS, and hand-checked places that are
// always shown (merged with live OpenStreetMap results). Set `jumaat: true` on a
// surau once you've confirmed it holds Friday prayers so it shows as confirmed
// for everyone. Coordinates are approximate — add more as you verify them.
window.JUMAAT_PRESETS = [
  { id: "midvalley", name: "Mid Valley Megamall", lat: 3.1179, lng: 101.6768 },
  { id: "gardens", name: "The Gardens Mall", lat: 3.1185, lng: 101.6755 },
  { id: "bangsarsouth", name: "Bangsar South", lat: 3.1110, lng: 101.6655 },
  { id: "klsentral", name: "KL Sentral", lat: 3.1340, lng: 101.6865 },
  { id: "klcc", name: "KLCC", lat: 3.1579, lng: 101.7116 },
  { id: "oneutama", name: "1 Utama, Petaling Jaya", lat: 3.1502, lng: 101.6152 },
  { id: "shahalam", name: "Shah Alam (Seksyen 7)", lat: 3.0738, lng: 101.4920 },
  { id: "bangi", name: "Bandar Baru Bangi", lat: 2.9622, lng: 101.7731 },
];

window.JUMAAT_SEED = [
  {
    name: "Masjid Jamek Abdullah Hukum",
    lat: 3.1172,
    lng: 101.6738,
    kind: "masjid",
    jumaat: true,
    info: "KL Eco City, beside Mid Valley / The Gardens. Prayer hall sits on top of a car park podium; linked bridge to Abdullah Hukum LRT/KTM.",
  },
];
