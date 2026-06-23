export function scrollToTripInspectionSection() {
  const el = document.querySelector('[id^="trip-inspection-"]');
  el?.scrollIntoView({ behavior: "smooth", block: "start" });
}
