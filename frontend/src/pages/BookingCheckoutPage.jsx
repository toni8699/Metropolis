import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, Star } from "lucide-react";
import { differenceInDays, format, parseISO } from "date-fns";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { apiGet, apiPost } from "../utils/api";
import { useAuth } from "../context/AuthContext";

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

  const startDate = location.state?.startDate;
  const endDate = location.state?.endDate;

  useEffect(() => {
    if (!isAuthenticated) {
      navigate(`/listings/${id}`, { replace: true });
      return;
    }
    if (!startDate || !endDate) {
      navigate(`/listings/${id}`, { replace: true });
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
  const dayCount = Math.max(1, start && end ? differenceInDays(end, start) : 1);
  const pricePerDay = Number(listing?.pricePerDay || 0);
  const subtotal = pricePerDay * dayCount;
  const cleaningFee = 50;
  const serviceFee = Number((subtotal * 0.1).toFixed(2));
  const total = Number((subtotal + cleaningFee + serviceFee).toFixed(2));

  const formattedDateRange =
    start && end ? `${format(start, "MMM d, yyyy")} - ${format(end, "MMM d, yyyy")}` : "";

  const handleRequestBooking = async () => {
    if (!listing) return;
    setSubmitError("");
    setIsSubmitting(true);
    try {
      await apiPost(
        "/api/bookings",
        {
          // Backend currently expects camelCase fields:
          listingId: Number(id),
          startAt: start.toISOString(),
          endAt: end.toISOString(),
        },
        true,
      );
      navigate("/trips");
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
        to={`/listings/${id}`}
        className="inline-flex items-center gap-2 text-sm font-medium text-gray-700 hover:underline"
      >
        <ChevronLeft className="h-4 w-4" />
        back to listing
      </Link>

      <div className="relative mt-6 flex flex-col-reverse gap-12 md:flex-row">
        <section className="w-full md:w-[55%]">
          <h1 className="mb-8 text-3xl font-semibold text-gray-900">Request to book</h1>

          <div className="pb-6">
            <h2 className="mb-4 text-xl font-semibold text-gray-900">Your trip</h2>
            <div className="flex items-center justify-between">
              <p className="font-medium text-gray-900">Dates</p>
              <p className="text-sm text-gray-700">{formattedDateRange}</p>
            </div>
          </div>

          <div className="border-t py-6">
            <h2 className="mb-4 text-xl font-semibold text-gray-900">Pay with</h2>
            <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-gray-50 p-4">
              <span className="text-sm font-medium text-gray-800">
                Credit Card ending in •••• 4242
              </span>
            </div>
          </div>

          <div className="border-t py-6">
            <p className="text-sm leading-6 text-gray-600">
              By selecting the button below, I agree to the Host&apos;s House Rules,
              Ground rules for guests, and DriveBnb&apos;s policies.
            </p>

            {submitError && (
              <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-600">
                {submitError}
              </div>
            )}

            <button
              onClick={handleRequestBooking}
              disabled={isSubmitting}
              className="mt-6 w-full rounded-xl bg-indigo-600 px-8 py-4 text-lg font-bold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40 md:w-auto"
            >
              {isSubmitting ? "Requesting..." : "Request to book"}
            </button>
          </div>
        </section>

        <aside className="w-full md:w-[45%]">
          <div className="sticky top-28 h-fit rounded-2xl border border-gray-200 bg-white p-6 shadow-xl">
            <div className="flex gap-4">
              <img
                src={listing.photos?.[0] || "https://placehold.co/240x180?text=Car"}
                alt={listing.title}
                className="h-20 w-24 rounded-lg object-cover"
              />
              <div className="min-w-0">
                <p className="truncate font-semibold text-gray-900">
                  {listing.make || listing.brand} {listing.model} {listing.year || ""}
                </p>
                <p className="truncate text-sm text-gray-500">
                  {listing.sourceType === "FLEET" ? "Fleet vehicle" : "Hosted vehicle"}
                </p>
                <p className="mt-1 flex items-center gap-1 text-sm text-gray-700">
                  <Star className="h-4 w-4 fill-current" />
                  4.90
                </p>
              </div>
            </div>

            <div className="my-6 border-b" />

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
                <p>DriveBnb service fee</p>
                <p>${serviceFee.toFixed(2)}</p>
              </div>
            </div>

            <div className="my-4 border-b" />

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
