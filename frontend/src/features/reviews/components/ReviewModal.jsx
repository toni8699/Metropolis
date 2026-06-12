import { useEffect, useState } from "react";
import { Star, X } from "lucide-react";
import { apiPost } from "@/shared/api/api";

function StarRatingRow({ label, value, onChange, disabled }) {
  const [hoverRating, setHoverRating] = useState(0);
  const displayRating = hoverRating || value;

  return (
    <div>
      <p className="mb-2 text-sm font-medium text-gray-900">{label}</p>
      <div className="flex items-center gap-2">
        {Array.from({ length: 5 }).map((_, index) => {
          const starValue = index + 1;
          const active = starValue <= displayRating;
          return (
            <button
              key={starValue}
              type="button"
              disabled={disabled}
              onClick={() => onChange(starValue)}
              onMouseEnter={() => setHoverRating(starValue)}
              onMouseLeave={() => setHoverRating(0)}
              className="rounded p-1 transition hover:scale-105 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label={`${label}: ${starValue} star${starValue === 1 ? "" : "s"}`}
            >
              <Star
                className={`h-7 w-7 ${
                  active ? "fill-gray-900 text-gray-900" : "text-gray-300"
                }`}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function ReviewModal({
  booking,
  isOpen,
  onClose,
  onSuccess,
  targetType = "LISTING",
}) {
  const [rating, setRating] = useState(0);
  const [cleanliness, setCleanliness] = useState(0);
  const [accuracy, setAccuracy] = useState(0);
  const [communication, setCommunication] = useState(0);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const normalizedTarget = String(targetType || "LISTING").toUpperCase();
  const isListingReview = normalizedTarget === "LISTING";

  useEffect(() => {
    if (!isOpen) return;
    setRating(0);
    setCleanliness(0);
    setAccuracy(0);
    setCommunication(0);
    setComment("");
    setError("");
    setIsSubmitting(false);
  }, [isOpen, booking?.bookingId]);

  if (!isOpen || !booking) return null;

  const title = booking.listingTitle || "your trip";

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!rating) {
      setError("Please select an overall experience rating.");
      return;
    }
    if (!comment.trim()) {
      setError("Please write a short comment about your trip.");
      return;
    }

    const payload = {
      targetType: normalizedTarget,
      rating,
      comment: comment.trim(),
    };
    if (cleanliness) payload.cleanliness = cleanliness;
    if (communication) payload.communication = communication;
    if (isListingReview && accuracy) payload.accuracy = accuracy;

    setIsSubmitting(true);
    try {
      await apiPost(`/api/bookings/${booking.bookingId}/reviews`, payload, true);
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err?.message || "Could not submit review.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[120] flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="review-modal-title"
    >
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 id="review-modal-title" className="text-xl font-semibold text-gray-900">
            Review your trip
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-full p-2 text-gray-500 hover:bg-gray-100"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 px-6 py-6">
          <p className="text-sm text-gray-600">
            How was <span className="font-medium text-gray-900">{title}</span>? Reviews are
            optional and can be submitted within 30 days after checkout.
          </p>

          <div className="space-y-4">
            <StarRatingRow
              label="Overall experience"
              value={rating}
              onChange={setRating}
              disabled={isSubmitting}
            />
            <StarRatingRow
              label="Cleanliness"
              value={cleanliness}
              onChange={setCleanliness}
              disabled={isSubmitting}
            />
            {isListingReview && (
              <StarRatingRow
                label="Accuracy"
                value={accuracy}
                onChange={setAccuracy}
                disabled={isSubmitting}
              />
            )}
            <StarRatingRow
              label="Communication"
              value={communication}
              onChange={setCommunication}
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="review-comment" className="mb-2 block text-sm font-medium text-gray-900">
              Your review
            </label>
            <textarea
              id="review-comment"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              rows={5}
              placeholder="Share what went well and what could be better..."
              className="w-full resize-y rounded-xl border border-gray-300 px-4 py-3 text-gray-900 outline-none transition focus:border-gray-900 focus:ring-2 focus:ring-gray-900/10"
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
          )}

          <div className="flex justify-end gap-3 border-t border-gray-100 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? "Submitting..." : "Submit review"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
