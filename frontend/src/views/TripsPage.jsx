import { useCallback, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import ReviewModal from "@/features/reviews/components/ReviewModal";
import { apiGet } from "@/shared/api/api";
import { bookingStatusBadgeClass, formatBookingStatusLabel } from "@/shared/lib/bookingStatus";

function formatTripDates(startAt, endAt) {
  if (!startAt || !endAt) return "Dates unavailable";
  const start = String(startAt).slice(0, 10);
  const end = String(endAt).slice(0, 10);
  return `${start} → ${end}`;
}

export default function TripsPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [trips, setTrips] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [reviewBooking, setReviewBooking] = useState(null);

  const loadTrips = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const data = await apiGet("/api/bookings/mine", true);
      setTrips(data?.bookings || []);
    } catch (err) {
      setTrips([]);
      setError(err?.message || "Could not load your trips.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    loadTrips();
  }, [isAuthenticated, loadTrips]);

  if (authLoading) {
    return (
      <div className="mx-auto max-w-3xl py-12 text-center text-sm text-gray-500">
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900">Your trips</h1>
        <p className="mt-2 text-gray-600">
          Track past and upcoming bookings. Reviews are optional and available for 30 days
          after a completed trip.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
      )}

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div
              key={idx}
              className="animate-pulse rounded-2xl border border-gray-200 bg-white p-6"
            >
              <div className="h-5 w-1/2 rounded bg-gray-200" />
              <div className="mt-3 h-4 w-1/3 rounded bg-gray-100" />
            </div>
          ))}
        </div>
      ) : trips.length === 0 ? (
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center">
          <p className="text-gray-600">No trips yet.</p>
          <Link
            to="/"
            className="mt-4 inline-block rounded-lg bg-indigo-600 px-5 py-2.5 font-medium text-white hover:bg-indigo-700"
          >
            Find a car
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {trips.map((trip) => (
            <article
              key={trip.bookingId}
              className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {trip.listingTitle || `Listing #${trip.listingId}`}
                  </h2>
                  <p className="mt-1 text-sm text-gray-600">
                    {formatTripDates(trip.startAt, trip.endAt)}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold tracking-wide ${bookingStatusBadgeClass(trip.status)}`}
                >
                  {formatBookingStatusLabel(trip.status)}
                </span>
              </div>

              <div className="mt-5 flex flex-wrap items-center gap-3">
                <Link
                  to={`/app/listings/${trip.listingId}`}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
                >
                  View listing
                </Link>
                <Link
                  to={`/app/bookings/${trip.bookingId}`}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Trip details
                </Link>
                {trip.needsReview && (
                  <button
                    type="button"
                    onClick={() => setReviewBooking(trip)}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                  >
                    Write a Review
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      <ReviewModal
        booking={reviewBooking}
        isOpen={Boolean(reviewBooking)}
        onClose={() => setReviewBooking(null)}
        onSuccess={loadTrips}
      />
    </div>
  );
}
