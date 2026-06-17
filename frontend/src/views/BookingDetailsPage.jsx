import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import {
  Calendar,
  CarFront,
  ChevronLeft,
  CreditCard,
  Mail,
  MapPin,
  ShieldCheck,
} from "lucide-react";
import { GoogleMap, Marker } from "@react-google-maps/api";
import BookingChat from "@/features/bookings/components/BookingChat";
import { useAuth } from "@/context/AuthContext";
import { useGoogleMaps } from "@/context/GoogleMapsProvider";
import { apiGet, apiPatch } from "@/shared/api/api";
import {
  bookingStatusBadgeClass,
  buildTripTimeline,
  formatMoney,
  formatTripEventAt,
  formatTripWindow,
  formatBookingStatusLabel,
} from "@/shared/lib/tripDetail";

const mapContainerStyle = { width: "100%", height: "100%" };

function PickupMap({ lat, lng }) {
  const { apiKey, isLoaded, loadError } = useGoogleMaps();

  if (!apiKey || lat == null || lng == null) {
    return (
      <div className="flex h-48 items-center justify-center rounded-2xl border-2 border-dashed border-black bg-vroom-card text-sm text-vroom-muted">
        Map unavailable
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="flex h-48 items-center justify-center rounded-2xl border-2 border-dashed border-black bg-vroom-card px-4 text-center text-sm text-vroom-muted">
        Could not load map
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="flex h-48 items-center justify-center rounded-2xl border-2 border-black bg-vroom-card text-sm text-vroom-muted">
        Loading map...
      </div>
    );
  }

  const center = { lat: Number(lat), lng: Number(lng) };
  return (
    <div className="h-48 overflow-hidden rounded-2xl border-2 border-black">
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        center={center}
        zoom={14}
        options={{
          disableDefaultUI: true,
          zoomControl: true,
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: false,
        }}
      >
        <Marker position={center} />
      </GoogleMap>
    </div>
  );
}

export default function BookingDetailsPage() {
  const { bookingId } = useParams();
  const { isAuthenticated, user } = useAuth();

  const [booking, setBooking] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [isActing, setIsActing] = useState(false);

  const load = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const data = await apiGet(`/api/bookings/${bookingId}`, true);
      setBooking(data?.booking || null);
    } catch (err) {
      setBooking(null);
      setError(err?.message || "Could not load trip details.");
    } finally {
      setIsLoading(false);
    }
  }, [bookingId]);

  useEffect(() => {
    if (!isAuthenticated) return;
    load();
  }, [isAuthenticated, load]);

  const timeline = useMemo(() => buildTripTimeline(booking), [booking]);
  const userRole = booking?.userRole;
  const isRenter = userRole === "renter";
  const isHost = userRole === "host";
  const location = booking?.listingLocation;
  const pricing = booking?.pricing;
  const earnings = booking?.earnings;
  const host = booking?.host;
  const renter = booking?.renter;

  const runAction = async (body = {}) => {
    setActionError("");
    setIsActing(true);
    try {
      await apiPatch(`/api/bookings/${bookingId}`, body, true);
      await load();
    } catch (err) {
      setActionError(err?.message || "Action failed.");
    } finally {
      setIsActing(false);
    }
  };

  const hasHostActions =
    isHost && (booking?.canApprove || booking?.canReject);
  const hasRenterActions =
    isRenter &&
    (booking?.canCancel || booking?.canConfirmPickup || booking?.canCompleteTrip);
  const hasAnyActions = hasHostActions || hasRenterActions;

  if (!isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl animate-pulse space-y-3 py-4">
        <div className="h-8 w-48 rounded bg-gray-200" />
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="h-80 rounded-2xl bg-gray-100" />
          <div className="h-80 rounded-2xl bg-gray-100" />
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="mx-auto max-w-3xl py-8">
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error || "Trip not found."}
        </p>
        <Link to="/app/trips" className="mt-4 inline-block text-sm font-semibold text-gray-700 underline">
          Back to trips
        </Link>
      </div>
    );
  }

  const cityLabel = location?.cityZone
    ? location.cityZone.replace(/-/g, " ")
    : booking.cityZone?.replace(/-/g, " ");

  const backPath = isHost ? "/host/dashboard" : "/app/trips";
  const backLabel = isHost ? "Host bookings" : "Your trips";

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <Link
        to={backPath}
        className="inline-flex items-center gap-2 rounded-full border-2 border-black bg-vroom-surface px-4 py-2 text-sm font-semibold text-vroom-heading shadow-neoSm"
      >
        <ChevronLeft className="h-4 w-4" />
        {backLabel}
      </Link>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-3">
          <section className="overflow-hidden rounded-3xl border-2 border-black bg-vroom-surface shadow-neoCard">
            <div className="grid md:grid-cols-[190px_1fr]">
              <div className="relative min-h-[150px] bg-gray-100 md:min-h-full">
                {booking.listingPhoto ? (
                  <img
                    src={booking.listingPhoto}
                    alt={booking.listingTitle || "Vehicle"}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full min-h-[150px] items-center justify-center text-gray-400">
                    <CarFront className="h-9 w-9" />
                  </div>
                )}
              </div>
              <div className="space-y-2.5 p-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Trip #{booking.bookingId}
                    </p>
                    <h1 className="mt-1 text-2xl font-extrabold text-vroom-heading">
                      {booking.listingTitle || "Your trip"}
                    </h1>
                    <p className="mt-1.5 flex items-center gap-1.5 text-xs text-gray-600">
                      <Calendar className="h-4 w-4" />
                      {formatTripWindow(booking.startAt, booking.endAt)}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${bookingStatusBadgeClass(booking.status)}`}
                  >
                    {formatBookingStatusLabel(booking.status)}
                  </span>
                </div>
                {isRenter && host && (
                  <div className="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3 text-sm text-gray-700">
                    <p className="font-semibold text-gray-900">
                      Host: {host.name || "VROOM Host"}
                      {host.verified && (
                        <span className="ml-2 inline-flex items-center gap-1 text-xs font-medium text-emerald-700">
                          <ShieldCheck className="h-3.5 w-3.5" />
                          Verified
                        </span>
                      )}
                    </p>
                    {host.email && (
                      <a
                        href={`mailto:${host.email}`}
                        className="mt-1 inline-flex items-center gap-1 text-gray-600 hover:text-gray-900"
                      >
                        <Mail className="h-3.5 w-3.5" />
                        {host.email}
                      </a>
                    )}
                  </div>
                )}
                {isHost && renter && (
                  <div className="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3 text-sm text-gray-700">
                    <p className="font-semibold text-gray-900">
                      Renter: {renter.name || "Guest renter"}
                    </p>
                    {renter.email && (
                      <a
                        href={`mailto:${renter.email}`}
                        className="mt-1 inline-flex items-center gap-1 text-gray-600 hover:text-gray-900"
                      >
                        <Mail className="h-3.5 w-3.5" />
                        {renter.email}
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="rounded-3xl border-2 border-black bg-vroom-surface p-4 shadow-neoCard">
            <h2 className="text-lg font-extrabold text-vroom-heading">Pickup & location</h2>
            <p className="mt-1 text-sm text-gray-600">
              {location?.pickupAddress || cityLabel || "Pickup location shared below"}
            </p>
            <div className="mt-3">
              <PickupMap lat={location?.lat} lng={location?.lng} />
            </div>
            {(cityLabel || location?.pickupAddress) && (
              <p className="mt-2.5 flex items-start gap-1.5 text-xs text-gray-700">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-gray-500" />
                <span>
                  {[location?.pickupAddress, cityLabel].filter(Boolean).join(" · ")}
                </span>
              </p>
            )}
            {booking.pickupNotes && (
              <div className="mt-3 rounded-xl border border-amber-100 bg-amber-50 px-3 py-2.5 text-xs text-amber-950">
                <p className="font-semibold">Host pickup notes</p>
                <p className="mt-1 whitespace-pre-wrap">{booking.pickupNotes}</p>
              </div>
            )}
          </section>

          <section className="rounded-3xl border-2 border-black bg-vroom-surface p-4 shadow-neoCard">
            <h2 className="text-lg font-extrabold text-vroom-heading">Trip timeline</h2>
            {timeline.length === 0 ? (
              <p className="mt-4 text-sm text-gray-500">No activity yet.</p>
            ) : (
              <ol className="mt-4 space-y-0">
                {timeline.map((item, index) => (
                  <li key={item.id} className="relative flex gap-3 pb-4 last:pb-0">
                    {index < timeline.length - 1 && (
                      <span
                        className="absolute left-[5px] top-2.5 h-[calc(100%-2px)] w-px bg-gray-200"
                        aria-hidden
                      />
                    )}
                    <span
                      className={`relative z-10 mt-1 h-2.5 w-2.5 shrink-0 rounded-full border ${
                        item.kind === "instruction"
                          ? "border-vroom-accent bg-vroom-accent"
                          : "border-vroom-muted bg-vroom-surface"
                      }`}
                    />
                    <div>
                      <p className="text-xs font-semibold text-gray-900">{item.title}</p>
                      <p className="text-xs text-gray-500">
                        {formatTripEventAt(item.at)}
                      </p>
                      {item.body && (
                        <p className="mt-1.5 rounded-lg bg-gray-50 px-2.5 py-1.5 text-xs text-gray-700">
                          {item.body}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <BookingChat
            bookingId={booking.bookingId}
            renterUserId={booking.renterUserId}
            hostUserId={booking.ownerUserId ?? booking.host?.userId}
            currentUserId={user?.userId}
          />
        </div>

        <aside className="space-y-3 lg:sticky lg:top-16 lg:self-start">
          <section className="rounded-3xl border-2 border-black bg-vroom-surface p-4 shadow-neoCard">
            <h2 className="text-lg font-extrabold text-vroom-heading">Actions</h2>
            {actionError && (
              <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{actionError}</p>
            )}
            <div className="mt-3 flex flex-col gap-1.5">
              {isHost && booking.canApprove && (
                <button
                  type="button"
                  disabled={isActing}
                  onClick={() => runAction({ status: "CONFIRMED" })}
                  className="rounded-full border-2 border-black border-b-4 bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white active:border-b-0 disabled:opacity-50"
                >
                  Approve booking
                </button>
              )}
              {isHost && booking.canReject && (
                <button
                  type="button"
                  disabled={isActing}
                  onClick={() => runAction({ status: "CANCELLED" })}
                  className="rounded-full border-2 border-black border-b-4 bg-vroom-error px-3 py-1.5 text-xs font-bold text-vroom-errorText active:border-b-0 disabled:opacity-50"
                >
                  Reject booking
                </button>
              )}
              {isRenter && booking.canCancel && (
                <button
                  type="button"
                  disabled={isActing}
                  onClick={() => runAction({ status: "CANCELLED" })}
                  className="rounded-full border-2 border-black border-b-4 bg-vroom-error px-3 py-1.5 text-xs font-bold text-vroom-errorText active:border-b-0 disabled:opacity-50"
                >
                  Cancel booking
                </button>
              )}
              {isRenter && booking.canConfirmPickup && (
                <button
                  type="button"
                  disabled={isActing}
                  onClick={() => runAction({ status: "IN_PROGRESS" })}
                  className="rounded-full border-2 border-black border-b-4 bg-vroom-heading px-3 py-1.5 text-xs font-bold text-white active:border-b-0 disabled:opacity-50"
                >
                  Confirm pickup
                </button>
              )}
              {isRenter && booking.canCompleteTrip && (
                <button
                  type="button"
                  disabled={isActing}
                  onClick={() => runAction({ status: "COMPLETED" })}
                  className="rounded-full border-2 border-black border-b-4 bg-vroom-accent px-3 py-1.5 text-xs font-extrabold text-white active:border-b-0 disabled:opacity-50"
                >
                  Complete trip
                </button>
              )}
              {!hasAnyActions && (
                <p className="text-sm text-gray-500">
                  No actions available for this trip right now.
                </p>
              )}
              <Link
                to={`/app/listings/${booking.listingId}`}
                className="rounded-full border-2 border-black border-b-4 bg-vroom-sage px-3 py-1.5 text-center text-xs font-bold text-vroom-heading active:border-b-0"
              >
                View listing
              </Link>
            </div>
          </section>

          <section className="rounded-3xl border-2 border-black bg-vroom-surface p-4 shadow-neoCard">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-gray-900">
                {isHost ? "Earnings Summary" : "Payment Summary"}
              </h2>
              {!isHost && (
                <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold text-gray-700">
                  <CreditCard className="h-3.5 w-3.5" />
                  Paid with card
                </span>
              )}
            </div>
            {isHost && earnings ? (
              <dl className="mt-3 space-y-2.5 text-xs">
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-600">
                    {formatMoney(earnings.pricePerDay, earnings.currency)} × {earnings.dayCount}{" "}
                    {earnings.dayCount === 1 ? "day" : "days"}
                  </dt>
                  <dd className="font-medium text-gray-900">
                    {formatMoney(earnings.subtotal, earnings.currency)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-600">Cleaning fee</dt>
                  <dd className="font-medium text-gray-900">
                    {formatMoney(earnings.cleaningFee, earnings.currency)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4 border-t border-gray-200 pt-2.5 text-xs">
                  <dt className="font-semibold text-gray-900">Gross host payout</dt>
                  <dd className="font-semibold text-gray-900">
                    {formatMoney(earnings.grossPayout, earnings.currency)}
                  </dd>
                </div>
              </dl>
            ) : !isHost && pricing ? (
              <dl className="mt-3 space-y-2.5 text-xs">
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-600">
                    {formatMoney(pricing.pricePerDay, pricing.currency)} × {pricing.dayCount}{" "}
                    {pricing.dayCount === 1 ? "day" : "days"}
                  </dt>
                  <dd className="font-medium text-gray-900">
                    {formatMoney(pricing.subtotal, pricing.currency)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-600">Service fee</dt>
                  <dd className="font-medium text-gray-900">
                    {formatMoney(pricing.serviceFee, pricing.currency)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-600">Cleaning fee</dt>
                  <dd className="font-medium text-gray-900">
                    {formatMoney(pricing.cleaningFee, pricing.currency)}
                  </dd>
                </div>
                {pricing.securityDeposit > 0 && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-gray-600">Security deposit</dt>
                    <dd className="font-medium text-gray-900">
                      {formatMoney(pricing.securityDeposit, pricing.currency)}
                    </dd>
                  </div>
                )}
                <div className="flex justify-between gap-4 border-t border-gray-200 pt-2.5 text-xs">
                  <dt className="font-semibold text-gray-900">Total</dt>
                  <dd className="font-semibold text-gray-900">
                    {formatMoney(pricing.total, pricing.currency)}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="mt-4 text-sm text-gray-500">
                {isHost ? "Earnings details unavailable." : "Pricing details unavailable."}
              </p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
