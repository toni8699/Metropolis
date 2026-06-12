/** Client-side review form validation (sub-ratings optional, matching backend). */
export function validateReviewForm({ rating, targetType = "LISTING" }) {
  if (!rating || rating < 1) {
    return { ok: false, error: "Please select an overall experience rating." };
  }
  const normalized = String(targetType || "LISTING").toUpperCase();
  if (normalized !== "LISTING" && normalized !== "RENTER") {
    return { ok: false, error: "Invalid review target." };
  }
  return { ok: true, error: null };
}
