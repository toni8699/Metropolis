/** Human-readable booking status for UI pills. */
export function formatBookingStatusLabel(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized === "PENDING") return "Awaiting payment";
  if (normalized === "PENDING_APPROVAL") return "Pending approval";
  if (normalized === "IN_PROGRESS") return "In Progress";
  return normalized.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export function bookingStatusBadgeClass(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized === "PENDING_APPROVAL") return "bg-amber-100 text-amber-900";
  if (normalized === "COMPLETED") return "bg-emerald-100 text-emerald-800";
  if (normalized === "IN_PROGRESS") return "bg-blue-100 text-blue-800";
  if (normalized === "CONFIRMED") return "bg-indigo-100 text-indigo-800";
  if (normalized === "CANCELLED") return "bg-red-100 text-red-800";
  if (normalized === "PENDING") return "bg-gray-100 text-gray-700";
  return "bg-gray-100 text-gray-700";
}

export function isPendingApproval(status) {
  return String(status || "").toUpperCase() === "PENDING_APPROVAL";
}
