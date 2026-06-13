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
    <div className="mx-auto max-w-3xl space-y-6 rounded-[2rem] border-2 border-black bg-[#f5f5d0] p-6 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
      <div>
        <h1 className="text-4xl font-extrabold text-[#183B1E]">Your trips</h1>
        <p className="mt-2 text-[#35593b]">
          Track past and upcoming bookings. Reviews are optional and available for 30 days
          after a completed trip.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border-2 border-black bg-[#ffd8cf] px-4 py-3 text-sm font-semibold text-[#7a2215]">{error}</div>
      )}

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div
              key={idx}
              className="animate-pulse rounded-2xl border-2 border-black bg-[#FCFCE5] p-6"
            >
              <div className="h-5 w-1/2 rounded bg-gray-200" />
              <div className="mt-3 h-4 w-1/3 rounded bg-gray-100" />
            </div>
          ))}
        </div>
      ) : trips.length === 0 ? (
        <div className="rounded-3xl border-2 border-black bg-[#FCFCE5] p-8 text-center shadow-[6px_6px_0px_0px_rgba(24,59,30,0.4)]">
          <p className="font-semibold text-[#35593b]">No trips yet.</p>
          <Link
            to="/"
            className="mt-4 inline-block rounded-full border-2 border-black border-b-4 bg-[#E34B31] px-5 py-2.5 font-extrabold text-white active:border-b-0"
          >
            Find a car
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {trips.map((trip) => (
            <article
              key={trip.bookingId}
              className="rounded-3xl border-2 border-black bg-[#FCFCE5] p-6 shadow-[6px_6px_0px_0px_rgba(24,59,30,0.4)]"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-2xl font-extrabold text-[#183B1E]">
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
                  className="rounded-full border-2 border-black border-b-4 bg-white px-4 py-2 text-sm font-bold text-[#183B1E] active:border-b-0"
                >
                  View listing
                </Link>
                <Link
                  to={`/app/bookings/${trip.bookingId}`}
                  className="rounded-full border-2 border-black border-b-4 bg-[#dbe8be] px-4 py-2 text-sm font-bold text-[#183B1E] active:border-b-0"
                >
                  Trip details
                </Link>
                {trip.needsReview && (
                  <button
                    type="button"
                    onClick={() => setReviewBooking(trip)}
                    className="rounded-full border-2 border-black border-b-4 bg-[#E34B31] px-4 py-2 text-sm font-extrabold text-white active:border-b-0"
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
