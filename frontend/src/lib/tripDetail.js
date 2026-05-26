import { format, parseISO } from "date-fns";
import { bookingStatusBadgeClass, formatBookingStatusLabel } from "./bookingStatus";

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
    INSTRUCTION_SENT: "Pickup instruction added",
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
    items.push({
      id: `event-${event.eventId}`,
      at: event.eventAt,
      title: formatEventLabel(event.eventType),
      body: null,
      kind: "system",
    });
  });

  (booking?.instructions || []).forEach((instruction) => {
    items.push({
      id: `instruction-${instruction.instructionId}`,
      at: instruction.sentAt,
      title: "Pickup instruction",
      body: instruction.message,
      kind: "instruction",
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
