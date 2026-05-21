import { useMemo, useState } from "react";
import { Star } from "lucide-react";
import {
  formatReviewDate,
  formatRatingValue,
  getListingRating,
} from "../lib/listingRating";

const PREVIEW_COUNT = 6;
const TRUNCATE_LENGTH = 150;

function avatarInitials(name) {
  const parts = String(name || "G")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!parts.length) return "G";
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return `${parts[0].charAt(0)}${parts[1].charAt(0)}`.toUpperCase();
}

function ReviewComment({ comment }) {
  const [expanded, setExpanded] = useState(false);
  const text = (comment || "").trim();

  if (!text) {
    return <p className="text-sm italic text-gray-400">No written comment.</p>;
  }

  const isLong = text.length > TRUNCATE_LENGTH;
  const visibleText = expanded || !isLong ? text : `${text.slice(0, TRUNCATE_LENGTH).trim()}…`;

  return (
    <p className="text-gray-800 leading-relaxed">
      {visibleText}
      {isLong && !expanded && (
        <>
          {" "}
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="font-semibold text-gray-900 underline hover:text-black"
          >
            Show more &gt;
          </button>
        </>
      )}
    </p>
  );
}

function ReviewCard({ review }) {
  const displayName = review.authorName || "DriveBnb guest";

  return (
    <article>
      <div className="mb-4 flex items-center gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gray-200 object-cover text-lg font-semibold text-gray-500">
          {avatarInitials(displayName)}
        </div>
        <div className="flex flex-col">
          <p className="text-base font-semibold text-gray-900">{displayName}</p>
          <p className="text-sm text-gray-500">
            {formatReviewDate(review.createdAt)}
            {review.rating != null && (
              <span className="ml-2 text-gray-700">
                ★ {Number(review.rating)}
              </span>
            )}
          </p>
        </div>
      </div>
      <ReviewComment comment={review.comment} />
    </article>
  );
}

export default function ListingReviewsSection({ listing, reviews = [], isLoading }) {
  const { hasReviews, averageRating, reviewCount } = getListingRating(listing);
  const [showAll, setShowAll] = useState(false);

  const visibleReviews = useMemo(() => {
    if (showAll) return reviews;
    return reviews.slice(0, PREVIEW_COUNT);
  }, [reviews, showAll]);

  const canShowMore = reviews.length > PREVIEW_COUNT;

  return (
    <section className="border-t border-gray-200 py-8">
      {hasReviews ? (
        <h2 className="mb-8 flex items-center gap-2 text-2xl font-semibold text-gray-900">
          <Star className="h-6 w-6 fill-current" />
          {formatRatingValue(averageRating)} · {reviewCount} reviews
        </h2>
      ) : (
        <h2 className="mb-8 text-2xl font-semibold text-gray-900">Reviews</h2>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-x-16 gap-y-10 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="animate-pulse space-y-4">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-gray-200" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-32 rounded bg-gray-200" />
                  <div className="h-3 w-24 rounded bg-gray-100" />
                </div>
              </div>
              <div className="h-16 w-full rounded bg-gray-100" />
            </div>
          ))}
        </div>
      ) : reviews.length === 0 ? (
        <p className="text-sm text-gray-500">
          No reviews yet. Be the first to book and share feedback.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-x-16 gap-y-10 md:grid-cols-2">
            {visibleReviews.map((review) => (
              <ReviewCard key={review.reviewId} review={review} />
            ))}
          </div>

          {canShowMore && !showAll && (
            <div className="mt-10">
              <button
                type="button"
                onClick={() => setShowAll(true)}
                className="rounded-lg border border-gray-900 px-6 py-3 text-base font-semibold text-gray-900 transition hover:bg-gray-50"
              >
                Show all {reviewCount} reviews
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
