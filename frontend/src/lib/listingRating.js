export function getListingRating(listing) {
  const reviewCount = Number(listing?.reviewCount ?? 0);
  const averageRating = listing?.averageRating;
  const hasReviews = reviewCount > 0 && averageRating != null;

  return {
    reviewCount,
    averageRating: hasReviews ? Number(averageRating) : null,
    hasReviews,
  };
}

export function formatRatingValue(averageRating) {
  return Number(averageRating).toFixed(2);
}

export function formatReviewCount(count) {
  const total = Number(count);
  if (!total) return "No reviews yet";
  return `${total} review${total === 1 ? "" : "s"}`;
}

export function formatReviewDate(isoValue) {
  if (!isoValue) return "";
  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}
