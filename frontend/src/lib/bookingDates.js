/** yyyy-MM-dd → ISO datetimes for POST /api/bookings (local calendar days). */
export function bookingWindowFromDateStrings(startDate, endDate) {
  return {
    startAt: localDateToIso(startDate, 10),
    endAt: localDateToIso(endDate, 10),
  };
}

function localDateToIso(yyyyMmDd, hour) {
  const [year, month, day] = yyyyMmDd.split("-").map(Number);
  return new Date(year, month - 1, day, hour, 0, 0, 0).toISOString();
}
