export function buildRevenueSeries(bookings) {
  if (!bookings.length) {
    return [{ day: "—", revenue: 0 }];
  }
  const totals = {};
  for (const booking of bookings) {
    const day = formatShortDay(booking.createdAt || booking.startAt);
    const amount = Number(booking.priceSnapshot?.pricePerDay ?? 0);
    totals[day] = (totals[day] || 0) + amount;
  }
  return Object.entries(totals).map(([day, revenue]) => ({ day, revenue }));
}

export function buildBookingsByLocation(bookings) {
  if (!bookings.length) {
    return [{ location: "No bookings", bookings: 0 }];
  }
  const counts = {};
  for (const booking of bookings) {
    const location = booking.cityZone || booking.listingTitle || "Unknown";
    counts[location] = (counts[location] || 0) + 1;
  }
  return Object.entries(counts).map(([location, bookingsCount]) => ({
    location,
    bookings: bookingsCount,
  }));
}

export function formatShortDay(isoValue) {
  if (!isoValue) return "—";
  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function formatBookingWindow(startAt, endAt) {
  if (!startAt || !endAt) return "n/a";
  const start = String(startAt).slice(0, 10);
  const end = String(endAt).slice(0, 10);
  return `${start} to ${end}`;
}
