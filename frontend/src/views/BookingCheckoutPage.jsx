import { useEffect, useMemo, useState } from "react";
import { ChevronLeft } from "lucide-react";
import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import ListingRatingLine from "@/features/listings/components/ListingRatingLine";
import StripePaymentForm from "@/features/bookings/components/StripePaymentForm";
import { differenceInDays, format, parseISO } from "date-fns";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { bookingWindowFromDateStrings } from "@/shared/lib/bookingDates";
import { computeCheckoutTotals } from "@/shared/lib/checkoutPricing";
import { apiGet, apiPost } from "@/shared/api/api";
import { useAuth } from "@/context/AuthContext";

const stripePublishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || "";

function safeParseDate(value) {
  if (!value) return null;
  try {
    return parseISO(value);
  } catch {
    return null;
  }
}

export default function BookingCheckoutPage() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [listing, setListing] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [clientSecret, setClientSecret] = useState(null);

  const stripePromise = useMemo(
    () => (stripePublishableKey ? loadStripe(stripePublishableKey) : null),
    [],
  );

  const startDate = location.state?.startDate;
  const endDate = location.state?.endDate;

  useEffect(() => {
    if (!isAuthenticated) {
      navigate(`/app/listings/${id}`, { replace: true });
      return;
    }
    if (!startDate || !endDate) {
      navigate(`/app/listings/${id}`, { replace: true });
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    apiGet(`/api/market/listings/${id}`)
      .then((data) => {
        if (!cancelled) setListing(data?.listing || null);
      })
      .catch(() => {
        if (!cancelled) setListing(null);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id, startDate, endDate, navigate, isAuthenticated]);

  const start = safeParseDate(startDate);
  const end = safeParseDate(endDate);
  const rawDayCount = start && end ? differenceInDays(end, start) : 1;
  const pricePerDay = Number(listing?.pricePerDay || 0);
  const { subtotal, cleaningFee, serviceFee, total, dayCount } = computeCheckoutTotals(
    pricePerDay,
    rawDayCount,
  );

  const formattedDateRange =
    start && end ? `${format(start, "MMM d, yyyy")} - ${format(end, "MMM d, yyyy")}` : "";

  const handleRequestBooking = async () => {
    if (!listing || !startDate || !endDate) return;
    setSubmitError("");
    setIsSubmitting(true);
    try {
      const { startAt, endAt } = bookingWindowFromDateStrings(startDate, endDate);
      const bookingResp = await apiPost(
        "/api/bookings",
        {
          listingId: Number(id),
          startAt,
          endAt,
        },
        true,
      );
      const bookingId = bookingResp?.booking?.bookingId;
      if (!bookingId) {
        throw new Error("Booking was not created.");
      }
      const intent = await apiPost(`/api/bookings/${bookingId}/payment-intent`, {}, true);
      if (intent?.mock || !intent?.clientSecret) {
        navigate("/app/trips");
        return;
      }
      setClientSecret(intent.clientSecret);
    } catch (err) {
      setSubmitError(err?.message || "Could not request booking.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-4 pb-12 pt-24 sm:px-6 lg:px-10">
        <div className="space-y-5">
          <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
          <div className="h-10 w-56 animate-pulse rounded bg-gray-200" />
          <div className="grid gap-12 md:grid-cols-[1.2fr_1fr]">
            <div className="space-y-4">
              <div className="h-20 animate-pulse rounded bg-gray-100" />
              <div className="h-20 animate-pulse rounded bg-gray-100" />
              <div className="h-20 animate-pulse rounded bg-gray-100" />
            </div>
            <div className="h-80 animate-pulse rounded-2xl bg-gray-100" />
          </div>
        </div>
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="mx-auto max-w-6xl px-4 pb-12 pt-24 sm:px-6 lg:px-10">
        <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
          Could not load listing for checkout.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 pb-12 pt-24 sm:px-6 lg:px-10">
      <Link
        to={`/app/listings/${id}`}
        className="inline-flex items-center gap-2 rounded-full border-2 border-black bg-[#FCFCE5] px-4 py-2 text-sm font-semibold text-[#183B1E] shadow-[4px_4px_0px_0px_rgba(24,59,30,0.45)] hover:underline"
      >
        <ChevronLeft className="h-4 w-4" />
        back to listing
      </Link>

      <div className="relative mt-6 flex flex-col-reverse gap-12 md:flex-row">
        <section className="w-full md:w-[55%]">
          <h1 className="mb-8 text-4xl font-extrabold text-[#183B1E]">Confirm and pay</h1>

          <div className="pb-6">
            <h2 className="mb-4 text-2xl font-extrabold text-[#183B1E]">Your trip</h2>
            <div className="flex items-center justify-between">
              <p className="font-medium text-gray-900">Dates</p>
              <p className="text-sm text-gray-700">{formattedDateRange}</p>
            </div>
          </div>

          <div className="border-t-2 border-black py-6">
            <h2 className="mb-4 text-2xl font-extrabold text-[#183B1E]">Pay with</h2>
            {clientSecret && stripePromise ? (
              <Elements stripe={stripePromise} options={{ clientSecret }}>
                <StripePaymentForm
                  onSuccess={() => navigate("/app/trips")}
                  onError={setSubmitError}
                />
              </Elements>
            ) : (
              <p className="text-sm text-gray-600">
                {stripePublishableKey
                  ? "Confirm your booking to enter card details."
                  : "Dev mode: payment completes automatically when you confirm."}
              </p>
            )}
          </div>

          <div className="border-t-2 border-black py-6">
            <p className="text-sm leading-6 text-gray-600">
              By selecting the button below, I agree to the Host&apos;s House Rules,
              Ground rules for guests, and VROOM&apos;s policies.
            </p>

            {submitError && (
              <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-600">
                {submitError}
              </div>
            )}

            {!clientSecret && (
              <button
                onClick={handleRequestBooking}
                disabled={isSubmitting}
                className="mt-6 w-full rounded-full border-2 border-black border-b-4 bg-[#E34B31] px-8 py-4 text-lg font-extrabold text-white transition hover:translate-y-[-1px] active:translate-y-1 active:border-b-0 disabled:cursor-not-allowed disabled:opacity-40 md:w-auto"
              >
                {isSubmitting ? "Confirming..." : "Confirm and pay"}
              </button>
            )}
          </div>
        </section>

        <aside className="w-full md:w-[45%]">
          <div className="sticky top-28 h-fit rounded-[2rem] border-2 border-black bg-[#FCFCE5] p-6 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.5)]">
            <div className="flex gap-4">
              <img
                src={listing.photos?.[0] || "https://placehold.co/240x180?text=Car"}
                alt={listing.title}
                className="h-20 w-24 rounded-lg object-cover"
              />
              <div className="min-w-0">
                <p className="truncate font-extrabold text-black">
                  {listing.make || listing.brand} {listing.model} {listing.year || ""}
                </p>
                <p className="truncate text-sm text-gray-500">
                  {listing.sourceType === "FLEET" ? "Fleet vehicle" : "Hosted vehicle"}
                </p>
                <div className="mt-1">
                  <ListingRatingLine listing={listing} />
                </div>
              </div>
            </div>

            <div className="my-6 border-b-2 border-black" />

            <div className="space-y-3 text-sm text-gray-800">
              <div className="flex items-center justify-between">
                <p>
                  ${pricePerDay.toFixed(2)} CAD x {dayCount} days
                </p>
                <p>${subtotal.toFixed(2)}</p>
              </div>
              <div className="flex items-center justify-between">
                <p>Cleaning fee</p>
                <p>${cleaningFee.toFixed(2)}</p>
              </div>
              <div className="flex items-center justify-between">
                <p>VROOM service fee</p>
                <p>${serviceFee.toFixed(2)}</p>
              </div>
            </div>

            <div className="my-4 border-b-2 border-black" />

            <div className="flex items-center justify-between text-lg font-bold text-gray-900">
              <p>Total (CAD)</p>
              <p>${total.toFixed(2)}</p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
