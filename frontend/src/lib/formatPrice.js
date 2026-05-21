/** Normalize listing daily price for display (map pins, cards). */
export function formatPricePerDay(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0) return null;
  return Number.isInteger(n) ? String(n) : String(Math.round(n));
}
