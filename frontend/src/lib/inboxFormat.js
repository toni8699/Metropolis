import { format, isThisYear, isToday, isYesterday, parseISO } from "date-fns";
import { formatBookingStatusLabel } from "./bookingStatus";
import { formatTripWindow } from "./tripDetail";

export function formatInboxMessageTime(iso) {
  if (!iso) return "";
  try {
    const date = parseISO(String(iso));
    if (isToday(date)) return format(date, "h:mm a");
    if (isYesterday(date)) return "Yesterday";
    if (isThisYear(date)) return format(date, "MMM d");
    return format(date, "MMM d, yyyy");
  } catch {
    return "";
  }
}

export function formatThreadContextSubtitle(thread) {
  if (!thread) return "";
  const status = formatBookingStatusLabel(thread.status);
  const window = formatTripWindow(thread.startAt, thread.endAt);
  const city = thread.cityZone
    ? thread.cityZone.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
    : null;
  return [status, window, city].filter(Boolean).join(" · ");
}

export function tripPhaseLabel(status) {
  const key = String(status || "").toUpperCase();
  if (["CONFIRMED", "PENDING_APPROVAL"].includes(key)) return "Upcoming";
  if (key === "IN_PROGRESS") return "In progress";
  if (key === "COMPLETED") return "Past trip";
  if (key === "CANCELLED") return "Cancelled";
  return formatBookingStatusLabel(status);
}
