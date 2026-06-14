import { format, parseISO } from "date-fns";
import { bookingStatusBadgeClass, formatBookingStatusLabel } from "@/shared/lib/bookingStatus";

export { bookingStatusBadgeClass, formatBookingStatusLabel };

export function formatTripEventAt(isoString) {
  if (!isoString) return "";
  try {
    return format(parseISO(String(isoString)), "MMM d, yyyy · h:mm a");
  } catch {
    return String(isoString).slice(0, 16);
  }
}

export function formatTripWindow(startAt, endAt) {
  if (!startAt || !endAt) return "Dates unavailable";
  try {
    const start = parseISO(String(startAt));
    const end = parseISO(String(endAt));
    return `${format(start, "MMM d, yyyy")} → ${format(end, "MMM d, yyyy")}`;
  } catch {
    return `${String(startAt).slice(0, 10)} → ${String(endAt).slice(0, 10)}`;
  }
}

export function formatEventLabel(eventType) {
  const key = String(eventType || "").toUpperCase();
  const labels = {
    BOOKING_CREATED: "Trip created",
    BOOKING_CANCELLED: "Booking cancelled",
    INSTRUCTION_SENT: "Host shared pickup note",
    STATUS_IN_PROGRESS: "Trip started",
    STATUS_COMPLETED: "Trip completed",
    TRIP_COMPLETED: "Trip completed",
    STATUS_CANCELLED: "Booking cancelled",
  };
  return labels[key] || key.replace(/_/g, " ").toLowerCase();
}

export function buildTripTimeline(booking) {
  const items = [];

  (booking?.tripEvents || []).forEach((event) => {
    const eventType = String(event?.eventType || "").toUpperCase();
    const metadata = event?.metadata || {};
    const body =
      eventType === "INSTRUCTION_SENT" && typeof metadata.message === "string"
        ? metadata.message
        : null;
    items.push({
      id: `event-${event.eventId}`,
      at: event.eventAt,
      title: formatEventLabel(event.eventType),
      body,
      kind: eventType === "INSTRUCTION_SENT" ? "instruction" : "system",
    });
  });

  return items.sort((a, b) => new Date(a.at).getTime() - new Date(b.at).getTime());
}

export function formatMoney(amount, currency = "CAD") {
  const value = Number(amount || 0);
  return new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}
