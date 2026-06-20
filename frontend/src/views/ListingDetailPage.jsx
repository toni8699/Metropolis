import { useEffect, useMemo, useState } from "react";
import { CarFront, Fuel, Settings } from "lucide-react";
import UserAvatar from "@/shared/components/UserAvatar";
import { differenceInDays, format } from "date-fns";
import { useAuth } from "@/context/AuthContext";
import AuthModal from "@/shared/components/AuthModal";
import { useNavigate, useParams } from "react-router-dom";
import ListingReviewsSection from "@/features/listings/components/ListingReviewsSection";
import ListingRatingLine from "@/features/listings/components/ListingRatingLine";
import ListingPhotoGrid from "@/features/listings/components/ListingPhotoGrid";
import ListingBookingCard from "@/features/listings/components/ListingBookingCard";
import PageShell from "@/shared/components/PageShell";
import { apiGet } from "@/shared/api/api";
import { dateRangeOverlapsBooked } from "@/shared/lib/bookingDates";
import { computeCheckoutTotals } from "@/shared/lib/checkoutPricing";
import {
  buildBookedModifiers,
  buildListingDatePickerDisabled,
  defaultDateRangeFromToday,
} from "@/shared/lib/datePicker";
import { listingPhotos } from "@/shared/lib/listingPhotos";

export default function ListingDetailPage() {
  const navigate = useNavigate();
  const { isAuthenticated, ensureVerifiedEmail } = useAuth();
  const { listingId } = useParams();
  const [listing, setListing] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [bookedRanges, setBookedRanges] = useState([]);
  const [dateRange, setDateRange] = useState(defaultDateRangeFromToday);
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);
  const [reserveError, setReserveError] = useState("");
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [calendarMonths] = useState(() =>
    typeof window !== "undefined" && window.matchMedia("(min-width: 1024px)").matches ? 2 : 1,
  );

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    apiGet(`/api/listings/${listingId}`)
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
  }, [listingId]);

  useEffect(() => {
    let cancelled = false;
    setReviewsLoading(true);
    apiGet(`/api/listings/${listingId}/reviews`)
      .then((data) => {
        if (!cancelled) setReviews(data?.reviews || []);
      })
      .catch(() => {
        if (!cancelled) setReviews([]);
      })
      .finally(() => {
        if (!cancelled) setReviewsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [listingId]);

  useEffect(() => {
    let cancelled = false;
    apiGet(`/api/listings/${listingId}/booked-ranges`)
      .then((data) => {
        if (!cancelled) setBookedRanges(data?.ranges || []);
      })
      .catch(() => {
        if (!cancelled) setBookedRanges([]);
      });
    return () => {
      cancelled = true;
    };
  }, [listingId]);

  const calendarDisabledMatchers = useMemo(
    () => buildListingDatePickerDisabled(bookedRanges),
    [bookedRanges],
  );
  const calendarBookedModifiers = useMemo(
    () => buildBookedModifiers(bookedRanges),
    [bookedRanges],
  );

  useEffect(() => {
    if (!bookedRanges.length) return;
    setDateRange((prev) => {
      if (!dateRangeOverlapsBooked(prev.from, prev.to, bookedRanges)) return prev;
      return { from: undefined, to: undefined };
    });
  }, [bookedRanges]);

  const photoSets = useMemo(() => (listing ? listingPhotos(listing) : { grid: [], gallery: [] }), [listing]);
  const guidelinesText = useMemo(() => {
    const text = (listing?.guidelines || listing?.rules || "").trim();
    return text || null;
  }, [listing]);

  if (isLoading) {
    return (
      <PageShell maxWidth="7xl" card className="space-y-4 px-5 py-8 sm:px-7 lg:px-11">
        <div className="h-10 w-2/3 animate-pulse rounded bg-gray-200" />
        <div className="h-5 w-1/3 animate-pulse rounded bg-gray-100" />
        <div className="grid aspect-[2/1] grid-cols-1 gap-2 overflow-hidden rounded-2xl md:aspect-[2.1] md:grid-cols-4">
          {Array.from({ length: 5 }).map((_, idx) => (
            <div
              key={idx}
              className={`animate-pulse bg-gray-200 ${
                idx === 0 ? "h-full w-full md:col-span-2 md:row-span-2" : "hidden h-full w-full md:block"
              }`}
            />
          ))}
        </div>
      </PageShell>
    );
  }

  if (!listing) {
    return (
      <PageShell maxWidth="7xl" card className="px-5 py-8 sm:px-7 lg:px-11">
        <p className="neo-error">Listing not found.</p>
      </PageShell>
    );
  }

  const title =
    listing.listingTitle ||
    listing.title ||
    `${listing.make || listing.brand || "Car"} ${listing.model || ""} ${listing.year || ""}`.trim();
  const locationText = listing.cityZone ? listing.cityZone.replace(/-/g, " ") : "Location";
  const isCompanyFleet = listing.isCompanyOwned || listing.sourceType === "FLEET";
  const hostedByName = listing.ownerName?.trim() || null;
  const hostUser = isCompanyFleet
    ? { fullName: "Company fleet" }
    : { fullName: hostedByName, profilePhotoUrl: listing.ownerProfilePhotoUrl };

  const rawDayCount =
    dateRange.from && dateRange.to ? differenceInDays(dateRange.to, dateRange.from) : 0;
  const hasCompleteRange = Boolean(dateRange.from && dateRange.to && rawDayCount > 0);
  const pricing = hasCompleteRange
    ? computeCheckoutTotals(listing.pricePerDay, rawDayCount)
    : null;

  const handleDateRangeChange = (next) => {
    if (dateRangeOverlapsBooked(next.from, next.to, bookedRanges)) {
      setReserveError("Those dates are already booked. Please choose different dates.");
      return;
    }
    setReserveError("");
    setDateRange(next);
  };

  const goToCheckout = () => {
    if (!dateRange.from || !dateRange.to) return;
    navigate(`/app/book/${listingId}`, {
      state: {
        startDate: format(dateRange.from, "yyyy-MM-dd"),
        endDate: format(dateRange.to, "yyyy-MM-dd"),
      },
    });
  };

  const handleReserveClick = () => {
    if (!dateRange.from || !dateRange.to) {
      setReserveError("Please select both check-in and checkout dates.");
      return;
    }
    if (differenceInDays(dateRange.to, dateRange.from) <= 0) {
      setReserveError("Checkout date must be after check-in date.");
      return;
    }
    if (dateRangeOverlapsBooked(dateRange.from, dateRange.to, bookedRanges)) {
      setReserveError("Those dates are already booked. Please choose different dates.");
      return;
    }

    setReserveError("");
    if (!isAuthenticated) {
      setIsAuthModalOpen(true);
      return;
    }
    if (!ensureVerifiedEmail()) {
      return;
    }
    goToCheckout();
  };

  return (
    <>
      <PageShell maxWidth="7xl" card className="px-5 py-8 sm:px-7 lg:px-11">
        <h1 className="mb-2 text-5xl font-black text-vroom-text">{title}</h1>
        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-700">
          <ListingRatingLine listing={listing} />
          <span>·</span>
          <span className="font-medium capitalize">{locationText}</span>
        </div>

        <ListingPhotoGrid
          title={title}
          gridImages={photoSets.grid}
          galleryImages={photoSets.gallery}
          isGalleryOpen={isGalleryOpen}
          onOpenGallery={() => setIsGalleryOpen(true)}
          onCloseGallery={() => setIsGalleryOpen(false)}
        />

        <div className="relative mt-10 flex flex-col gap-12 md:flex-row">
          <div className="w-full space-y-6 md:w-[65%]">
            <div className="flex items-center gap-3 border-t-4 border-black py-6">
              <UserAvatar user={hostUser} className="h-10 w-10 text-sm" />
              <div>
                <p className="text-xl font-semibold text-vroom-heading">
                  {isCompanyFleet
                    ? "Company fleet"
                    : hostedByName
                      ? `Hosted by ${hostedByName}`
                      : "Individual host"}
                </p>
                {!isCompanyFleet && hostedByName && (
                  <p className="text-sm text-vroom-muted">Individual host</p>
                )}
              </div>
            </div>

            <div className="grid gap-4 border-t-4 border-black py-6 sm:grid-cols-3">
              <div className="flex items-center gap-2 rounded-full border-2 border-black bg-white px-4 py-2 font-bold text-vroom-text">
                <CarFront className="h-5 w-5 text-vroom-accent" />
                <span className="text-sm">{listing.seats ? `${listing.seats} seats` : "Seats N/A"}</span>
              </div>
              <div className="flex items-center gap-2 rounded-full border-2 border-black bg-white px-4 py-2 font-bold text-vroom-text">
                <Settings className="h-5 w-5 text-vroom-accent" />
                <span className="text-sm">{listing.transmission || "Transmission N/A"}</span>
              </div>
              <div className="flex items-center gap-2 rounded-full border-2 border-black bg-white px-4 py-2 font-bold text-vroom-text">
                <Fuel className="h-5 w-5 text-vroom-accent" />
                <span className="text-sm">{listing.fuelType || "Fuel N/A"}</span>
              </div>
            </div>

            <p className="text-base leading-7 text-gray-700">
              {listing.description ||
                "Enjoy a smooth and reliable ride. Perfect for city commutes or weekend escapes."}
            </p>

            {guidelinesText && (
              <section className="border-t-4 border-black py-6">
                <h2 className="mb-3 text-xl font-semibold text-vroom-heading">Guidelines</h2>
                <p className="whitespace-pre-wrap text-base leading-7 text-gray-700">{guidelinesText}</p>
              </section>
            )}

            <div className="grid gap-3 sm:grid-cols-2">
              {(Array.isArray(listing.features) && listing.features.length
                ? listing.features
                : []
              ).map((feature) => (
                <div key={feature} className="flex items-center gap-2 text-sm text-gray-800">
                  <span className="h-1.5 w-1.5 rounded-full bg-gray-900" />
                  {feature}
                </div>
              ))}
            </div>

            <ListingReviewsSection listing={listing} reviews={reviews} isLoading={reviewsLoading} />
          </div>

          <div className="w-full md:w-[35%]">
            <ListingBookingCard
              pricePerDay={listing.pricePerDay}
              dateRange={dateRange}
              onDateRangeChange={handleDateRangeChange}
              bookedRanges={bookedRanges}
              calendarDisabledMatchers={calendarDisabledMatchers}
              calendarBookedModifiers={calendarBookedModifiers}
              calendarMonths={calendarMonths}
              onReserve={handleReserveClick}
              reserveButtonDisabled={!dateRange.from || !dateRange.to}
              reserveError={reserveError}
              pricing={pricing}
              hasCompleteRange={hasCompleteRange}
            />
          </div>
        </div>
      </PageShell>
      <AuthModal
        isOpen={isAuthModalOpen}
        mode="login"
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={goToCheckout}
      />
    </>
  );
}
