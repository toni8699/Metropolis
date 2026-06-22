import { useCallback, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import ReviewModal from "@/features/reviews/components/ReviewModal";
import PageShell from "@/shared/components/PageShell";
import { apiGet, apiPatch } from "@/shared/api/api";
import { bookingStatusBadgeClass, formatBookingStatusLabel } from "@/shared/lib/bookingStatus";
import { formatTripWindow } from "@/shared/lib/tripDetail";

export default function TripsPage() {
  const { isAuthenticated } = useAuth();
  const [trips, setTrips] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [reviewBooking, setReviewBooking] = useState(null);
  const [cancellingId, setCancellingId] = useState(null);

  const loadTrips = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const data = await apiGet("/api/bookings?scope=mine", true);
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

  const handleCancel = async (bookingId) => {
    if (!window.confirm("Cancel this booking?")) return;
    setError("");
    setCancellingId(bookingId);
    try {
      await apiPatch(`/api/bookings/${bookingId}`, { status: "CANCELLED" }, true);
      await loadTrips();
    } catch (err) {
      setError(err?.message || "Could not cancel booking.");
    } finally {
      setCancellingId(null);
    }
  };

  if (!isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  return (
    <PageShell maxWidth="3xl" card className="space-y-6 p-6">
      <div>
        <h1 className="text-4xl font-extrabold text-vroom-heading">Your trips</h1>
        <p className="mt-2 text-vroom-muted">
          Track past and upcoming bookings. Reviews are optional and available for 30 days
          after a completed trip.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border-2 border-black bg-vroom-error px-4 py-3 text-sm font-semibold text-vroom-errorText">{error}</div>
      )}

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div
              key={idx}
              className="animate-pulse rounded-2xl border-2 border-black bg-vroom-surface p-6"
            >
              <div className="h-5 w-1/2 rounded bg-gray-200" />
              <div className="mt-3 h-4 w-1/3 rounded bg-gray-100" />
            </div>
          ))}
        </div>
      ) : trips.length === 0 ? (
        <div className="rounded-3xl border-2 border-black bg-vroom-surface p-8 text-center shadow-neoCard">
          <p className="font-semibold text-vroom-muted">No trips yet.</p>
          <Link
            to="/app"
            className="mt-4 inline-block rounded-full border-2 border-black border-b-4 bg-vroom-accent px-5 py-2.5 font-extrabold text-white active:border-b-0"
          >
            Find a car
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {trips.map((trip) => (
            <article
              key={trip.bookingId}
              className="rounded-3xl border-2 border-black bg-vroom-surface p-6 shadow-neoCard"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-2xl font-extrabold text-vroom-heading">
                    {trip.listingTitle || `Listing #${trip.listingId}`}
                  </h2>
                  <p className="mt-1 text-sm text-gray-600">
                    {formatTripWindow(trip.startAt, trip.endAt)}
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
                  className="rounded-full border-2 border-black border-b-4 bg-white px-4 py-2 text-sm font-bold text-vroom-heading active:border-b-0"
                >
                  View listing
                </Link>
                <Link
                  to={`/app/bookings/${trip.bookingId}`}
                  className="rounded-full border-2 border-black border-b-4 bg-vroom-sage px-4 py-2 text-sm font-bold text-vroom-heading active:border-b-0"
                >
                  Trip details
                </Link>
                {trip.needsReview && (
                  <button
                    type="button"
                    onClick={() => setReviewBooking(trip)}
                    className="rounded-full border-2 border-black border-b-4 bg-vroom-accent px-4 py-2 text-sm font-extrabold text-white active:border-b-0"
                  >
                    Write a Review
                  </button>
                )}
                {trip.canCancel && (
                  <button
                    type="button"
                    disabled={cancellingId === trip.bookingId}
                    onClick={() => handleCancel(trip.bookingId)}
                    className="rounded-full border-2 border-black border-b-4 bg-vroom-error px-4 py-2 text-sm font-bold text-vroom-errorText active:border-b-0 disabled:opacity-50"
                  >
                    {cancellingId === trip.bookingId ? "Cancelling..." : "Cancel booking"}
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
    </PageShell>
  );
}
