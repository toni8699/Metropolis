import { format } from "date-fns";

/** yyyy-MM-dd → ISO datetimes for POST /api/bookings (local calendar days). */
export function bookingWindowFromDateStrings(startDate, endDate) {
  return {
    startAt: localDateToIso(startDate, 10),
    endAt: localDateToIso(endDate, 10),
  };
}

/** True when [from, to] check-in/out days overlap an existing booking window. */
export function dateRangeOverlapsBooked(from, to, bookedRanges) {
  if (!from || !to || !bookedRanges?.length) {
    return false;
  }
  const { startAt, endAt } = bookingWindowFromDateStrings(
    format(from, "yyyy-MM-dd"),
    format(to, "yyyy-MM-dd"),
  );
  const newStart = new Date(startAt).getTime();
  const newEnd = new Date(endAt).getTime();
  return bookedRanges.some((range) => {
    const existingStart = new Date(range.startAt).getTime();
    const existingEnd = new Date(range.endAt).getTime();
    return existingStart < newEnd && existingEnd > newStart;
  });
}

function localDateToIso(yyyyMmDd, hour) {
  const [year, month, day] = yyyyMmDd.split("-").map(Number);
  return new Date(year, month - 1, day, hour, 0, 0, 0).toISOString();
}
