import { Star } from "lucide-react";
import {
  formatRatingValue,
  formatReviewCount,
  getListingRating,
} from "../lib/listingRating";

/** Compact rating + review count (listing cards, headers). */
export default function ListingRatingLine({ listing, className = "" }) {
  const { hasReviews, averageRating, reviewCount } = getListingRating(listing);

  if (!hasReviews) {
    return <span className={`text-sm text-gray-500 ${className}`.trim()}>New</span>;
  }

  return (
    <span className={`inline-flex items-center gap-1 text-sm font-medium text-gray-900 ${className}`.trim()}>
      <Star className="h-4 w-4 fill-current" />
      {formatRatingValue(averageRating)}
      <span className="font-normal text-gray-500">·</span>
      <span className="font-normal text-gray-700">{formatReviewCount(reviewCount)}</span>
    </span>
  );
}
