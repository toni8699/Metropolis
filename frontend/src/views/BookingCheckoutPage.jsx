import { useEffect, useMemo, useState } from "react";
import { ChevronLeft } from "lucide-react";
import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import ListingRatingLine from "@/features/listings/components/ListingRatingLine";
import PageShell from "@/shared/components/PageShell";
import PricingBreakdown from "@/shared/components/PricingBreakdown";
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
    apiGet(`/api/listings/${id}`)
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
      const intent = await apiPost(`/api/bookings/${bookingId}/payments`, {}, true);
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
      <PageShell maxWidth="6xl" card className="space-y-5 p-6">
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
      </PageShell>
    );
  }

  if (!listing) {
    return (
      <PageShell maxWidth="6xl" card className="p-6">
        <p className="neo-error">Could not load listing for checkout.</p>
      </PageShell>
    );
  }

  return (
    <PageShell maxWidth="6xl" card className="p-6">
      <Link
        to={`/app/listings/${id}`}
        className="inline-flex items-center gap-2 rounded-full border-2 border-black bg-vroom-surface px-4 py-2 text-sm font-semibold text-vroom-heading shadow-neoSm hover:underline"
      >
        <ChevronLeft className="h-4 w-4" />
        back to listing
      </Link>

      <div className="relative mt-6 flex flex-col-reverse gap-12 md:flex-row">
        <section className="w-full md:w-[55%]">
          <h1 className="mb-8 text-4xl font-extrabold text-vroom-heading">Confirm and pay</h1>

          <div className="pb-6">
            <h2 className="mb-4 text-2xl font-extrabold text-vroom-heading">Your trip</h2>
            <div className="flex items-center justify-between">
              <p className="font-medium text-gray-900">Dates</p>
              <p className="text-sm text-gray-700">{formattedDateRange}</p>
            </div>
          </div>

          <div className="border-t-2 border-black py-6">
            <h2 className="mb-4 text-2xl font-extrabold text-vroom-heading">Pay with</h2>
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

            {submitError && <p className="neo-error mt-4">{submitError}</p>}

            {!clientSecret && (
              <button
                onClick={handleRequestBooking}
                disabled={isSubmitting}
                className="neo-btn-primary mt-6 w-full border-2 px-8 py-4 text-lg md:w-auto"
              >
                {isSubmitting ? "Confirming..." : "Confirm and pay"}
              </button>
            )}
          </div>
        </section>

        <aside className="w-full md:w-[45%]">
          <div className="sticky top-6 h-fit rounded-[2rem] border-2 border-black bg-vroom-surface p-6 shadow-neo">
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

            <PricingBreakdown
              pricePerDay={pricePerDay}
              dayCount={dayCount}
              subtotal={subtotal}
              cleaningFee={cleaningFee}
              serviceFee={serviceFee}
              total={total}
              showNightsLabel={false}
            />
          </div>
        </aside>
      </div>
    </PageShell>
  );
}
