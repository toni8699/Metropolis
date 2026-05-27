import { useEffect, useMemo, useRef, useState } from "react";
import { CarFront, ChevronLeft, ChevronRight, Fuel, Settings, UserCircle2 } from "lucide-react";
import { differenceInCalendarDays, format } from "date-fns";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";
import { useAuth } from "../context/AuthContext";
import AuthModal from "../components/AuthModal";
import { useNavigate, useParams } from "react-router-dom";
import ListingReviewsSection from "../components/ListingReviewsSection";
import ListingRatingLine from "../components/ListingRatingLine";
import { apiGet } from "../utils/api";
import { dateRangeOverlapsBooked } from "../lib/bookingDates";
import {
  airbnbDayPickerClassNames,
  bookedDayModifierClassNames,
  buildBookedModifiers,
  buildListingDatePickerDisabled,
  defaultDateRangeFromToday,
  sanitizeDateRange,
  startOfToday,
} from "../lib/datePicker";

export default function ListingDetailPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { listingId } = useParams();
  const [listing, setListing] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [bookedRanges, setBookedRanges] = useState([]);
  const [dateRange, setDateRange] = useState(defaultDateRangeFromToday);
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);
  const [reserveError, setReserveError] = useState("");
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [calendarMonths, setCalendarMonths] = useState(2);
  const calendarRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    apiGet(`/api/market/listings/${listingId}`)
      .then((data) => {
        if (!cancelled) {
          setListing(data?.listing || null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setListing(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [listingId]);

  useEffect(() => {
    let cancelled = false;
    setReviewsLoading(true);
    apiGet(`/api/market/listings/${listingId}/reviews`)
      .then((data) => {
        if (!cancelled) {
          setReviews(data?.reviews || []);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setReviews([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setReviewsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [listingId]);

  useEffect(() => {
    let cancelled = false;
    apiGet(`/api/market/listings/${listingId}/booked-ranges`)
      .then((data) => {
        if (!cancelled) {
          setBookedRanges(data?.ranges || []);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setBookedRanges([]);
        }
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
      if (!dateRangeOverlapsBooked(prev.from, prev.to, bookedRanges)) {
        return prev;
      }
      return { from: undefined, to: undefined };
    });
  }, [bookedRanges]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!calendarRef.current?.contains(event.target)) {
        setIsCalendarOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const syncCalendarMonths = () => {
      setCalendarMonths(window.innerWidth >= 1024 ? 2 : 1);
    };
    syncCalendarMonths();
    window.addEventListener("resize", syncCalendarMonths);
    return () => window.removeEventListener("resize", syncCalendarMonths);
  }, []);

  useEffect(() => {
    if (!isGalleryOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isGalleryOpen]);

  const images = useMemo(() => {
    const raw = listing?.photos?.filter(Boolean) || [];
    if (raw.length >= 5) return raw.slice(0, 5);
    if (raw.length === 0) return Array.from({ length: 5 }).map(() => null);
    const repeated = [...raw];
    while (repeated.length < 5) {
      repeated.push(raw[repeated.length % raw.length]);
    }
    return repeated.slice(0, 5);
  }, [listing]);
  const guidelinesText = useMemo(() => {
    const text = (listing?.guidelines || listing?.rules || "").trim();
    return text || null;
  }, [listing]);

  const galleryImages = useMemo(() => {
    const all = [
      ...(Array.isArray(listing?.images) ? listing.images : []),
      ...(Array.isArray(listing?.photos) ? listing.photos : []),
    ].filter(Boolean);
    return Array.from(new Set(all));
  }, [listing?.images, listing?.photos]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-10">
        <div className="space-y-4">
          <div className="h-10 w-2/3 animate-pulse rounded bg-gray-200" />
          <div className="h-5 w-1/3 animate-pulse rounded bg-gray-100" />
          <div className="grid grid-cols-1 gap-2 overflow-hidden rounded-2xl aspect-[2/1] md:aspect-[2.1] md:grid-cols-4">
            {Array.from({ length: 5 }).map((_, idx) => (
              <div
                key={idx}
                className={`animate-pulse bg-gray-200 ${
                  idx === 0
                    ? "w-full h-full md:col-span-2 md:row-span-2"
                    : "hidden w-full h-full md:block"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-10">
        <p className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-600">
          Listing not found.
        </p>
      </div>
    );
  }

  const title =
    listing.title ||
    `${listing.make || listing.brand || "Car"} ${listing.model || ""} ${
      listing.year || ""
    }`.trim();
  const locationText = listing.cityZone ? listing.cityZone.replace(/-/g, " ") : "Location";
  const hostedByName = listing.isCompanyOwned ? "DriveBnb Fleet" : listing.ownerName || "DriveBnb Host";
  const hostRoleLabel = listing.isCompanyOwned ? "Company fleet" : "Individual host";

  const nights =
    dateRange.from && dateRange.to
      ? differenceInCalendarDays(dateRange.to, dateRange.from)
      : 0;
  const hasCompleteRange = Boolean(dateRange.from && dateRange.to && nights > 0);
  const nightlySubtotal = hasCompleteRange ? Number(listing.pricePerDay || 0) * nights : 0;
  const serviceFee = hasCompleteRange ? Number((nightlySubtotal * 0.12).toFixed(2)) : 0;
  const cleaningFee = hasCompleteRange ? 25 : 0;
  const totalPrice = hasCompleteRange
    ? Number((nightlySubtotal + serviceFee + cleaningFee).toFixed(2))
    : 0;

  const handleReserveClick = () => {
    if (!dateRange.from || !dateRange.to) {
      setReserveError("Please select both check-in and checkout dates.");
      return;
    }
    if (differenceInCalendarDays(dateRange.to, dateRange.from) <= 0) {
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

    goToCheckout();
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

  const reserveButtonDisabled = !dateRange.from || !dateRange.to;

  return (
    <>
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-10">
      <h1 className="mb-2 text-3xl font-semibold text-gray-900">{title}</h1>
      <div className="flex flex-wrap items-center gap-2 text-sm text-gray-700">
        <ListingRatingLine listing={listing} />
        <span>·</span>
        <span className="font-medium capitalize">{locationText}</span>
      </div>

      <div className="group relative mt-6 grid grid-cols-1 gap-2 overflow-hidden rounded-2xl aspect-[2/1] md:aspect-[2.1] md:grid-cols-4">
        {[0, 1, 2, 3, 4].map((index) => (
          <div
            key={index}
            className={`overflow-hidden ${
              index === 0
                ? "md:col-span-2 md:row-span-2 w-full h-full"
                : "hidden md:block w-full h-full"
            }`}
          >
            {images[index] ? (
              <img
                src={images[index]}
                alt={`${title} photo ${index + 1}`}
                className="w-full h-full object-cover cursor-pointer transition hover:opacity-90"
                onClick={() => setIsGalleryOpen(true)}
              />
            ) : (
              <div className="h-full w-full bg-gray-200" />
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={() => setIsGalleryOpen(true)}
          className="absolute bottom-4 right-4 flex items-center gap-2 rounded-lg border border-black bg-white px-4 py-1.5 text-sm font-semibold shadow-md transition hover:bg-gray-50"
        >
          <CarFront className="h-4 w-4" />
          Show all photos
        </button>
      </div>

      <div className="relative mt-10 flex flex-col gap-12 md:flex-row">
        <div className="w-full space-y-6 md:w-[65%]">
          <div className="flex items-center gap-3 border-b py-6">
            <UserCircle2 className="h-10 w-10 text-gray-500" />
            <div>
              <p className="text-xl font-semibold text-gray-900">
                Hosted by {hostedByName}
              </p>
              <p className="text-sm text-gray-500">
                {hostRoleLabel}
              </p>
            </div>
          </div>

          <div className="grid gap-4 border-b py-6 sm:grid-cols-3">
            <div className="flex items-center gap-2">
              <CarFront className="h-5 w-5 text-gray-700" />
              <span className="text-sm text-gray-700">5 seats</span>
            </div>
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-gray-700" />
              <span className="text-sm text-gray-700">Automatic</span>
            </div>
            <div className="flex items-center gap-2">
              <Fuel className="h-5 w-5 text-gray-700" />
              <span className="text-sm text-gray-700">
                {listing.make?.toLowerCase().includes("tesla") ? "Electric" : "Gas"}
              </span>
            </div>
          </div>

          <p className="text-base leading-7 text-gray-700">
            {listing.description ||
              "Enjoy a smooth and reliable ride. Perfect for city commutes or weekend escapes."}
          </p>

          {guidelinesText && (
            <section className="border-t border-gray-200 py-6">
              <h2 className="mb-3 text-xl font-semibold text-gray-900">Guidelines</h2>
              <p className="whitespace-pre-wrap text-base leading-7 text-gray-700">{guidelinesText}</p>
            </section>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            {(Array.isArray(listing.features) && listing.features.length
              ? listing.features
              : ["Instant booking", "Free cancellation in 24h"]
            ).map((feature) => (
              <div key={feature} className="flex items-center gap-2 text-sm text-gray-800">
                <span className="h-1.5 w-1.5 rounded-full bg-gray-900" />
                {feature}
              </div>
            ))}
          </div>

          <ListingReviewsSection
            listing={listing}
            reviews={reviews}
            isLoading={reviewsLoading}
          />
        </div>

        <div className="w-full md:w-[35%]">
          <div className="sticky top-28 rounded-2xl border border-gray-200 bg-white p-6 shadow-xl">
            <div className="flex items-baseline gap-1">
              <p className="text-2xl font-bold text-gray-900">${listing.pricePerDay}</p>
              <p className="text-gray-600">/ day</p>
            </div>

            <div ref={calendarRef} className="relative mt-6">
              <div
                className="flex border border-gray-400 rounded-xl cursor-pointer relative"
                onClick={() => setIsCalendarOpen((open) => !open)}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setIsCalendarOpen((open) => !open);
                  }
                }}
              >
                <div className="w-1/2 p-3">
                  <p className="text-[10px] font-bold text-gray-800">CHECK-IN</p>
                  <p className="text-sm text-gray-500">
                    {dateRange.from ? format(dateRange.from, "MM/dd/yyyy") : "Add date"}
                  </p>
                </div>
                <div className="w-1/2 p-3 border-l border-gray-400">
                  <p className="text-[10px] font-bold text-gray-800">CHECKOUT</p>
                  <p className="text-sm text-gray-500">
                    {dateRange.to ? format(dateRange.to, "MM/dd/yyyy") : "Add date"}
                  </p>
                </div>
              </div>

              {isCalendarOpen && (
                <div className="absolute top-[100%] right-0 mt-4 bg-white rounded-2xl shadow-2xl border border-gray-200 p-6 z-50">
                  <DayPicker
                    mode="range"
                    numberOfMonths={calendarMonths}
                    startMonth={startOfToday()}
                    disabled={calendarDisabledMatchers}
                    modifiers={calendarBookedModifiers}
                    modifiersClassNames={bookedDayModifierClassNames}
                    selected={dateRange}
                    onSelect={(range) => {
                      const next = sanitizeDateRange(range);
                      if (dateRangeOverlapsBooked(next.from, next.to, bookedRanges)) {
                        setReserveError(
                          "Those dates are already booked. Please choose different dates.",
                        );
                        return;
                      }
                      setReserveError("");
                      setDateRange(next);
                    }}
                    className="rdp-airbnb"
                    classNames={airbnbDayPickerClassNames(true)}
                    components={{
                      Chevron: ({ orientation, ...props }) =>
                        orientation === "left" ? (
                          <ChevronLeft {...props} className="h-5 w-5" />
                        ) : (
                          <ChevronRight {...props} className="h-5 w-5" />
                        ),
                    }}
                  />
                  <div className="flex justify-between items-center pt-4 border-t mt-4">
                    <button
                      type="button"
                      onClick={() => setDateRange(defaultDateRangeFromToday())}
                      className="underline font-medium text-sm cursor-pointer hover:text-black text-gray-600"
                    >
                      Clear dates
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsCalendarOpen(false)}
                      className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-black"
                    >
                      Close
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={handleReserveClick}
              disabled={reserveButtonDisabled}
              className="mt-4 w-full rounded-lg bg-indigo-600 py-3 font-bold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Reserve
            </button>
            <p className="mt-3 text-center text-sm text-gray-500">
              You won&apos;t be charged yet
            </p>
            {reserveError && (
              <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-600">
                {reserveError}
              </div>
            )}
            {hasCompleteRange ? (
              <div className="mt-5 space-y-3 border-t border-gray-200 pt-4 text-sm text-gray-700">
                <div className="flex items-center justify-between">
                  <p className="underline">
                    ${listing.pricePerDay} x {nights} nights
                  </p>
                  <p>${nightlySubtotal.toFixed(2)}</p>
                </div>
                <div className="flex items-center justify-between">
                  <p className="underline">Service fee</p>
                  <p>${serviceFee.toFixed(2)}</p>
                </div>
                <div className="flex items-center justify-between">
                  <p className="underline">Cleaning fee</p>
                  <p>${cleaningFee.toFixed(2)}</p>
                </div>
                <div className="flex items-center justify-between border-t border-gray-200 pt-3 text-base font-semibold text-gray-900">
                  <p>Total before taxes</p>
                  <p>${totalPrice.toFixed(2)}</p>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-center text-sm text-gray-500">Add dates to see price</p>
            )}
          </div>
        </div>
      </div>
      </div>
      {isGalleryOpen && (
        <div className="fixed inset-0 z-[100] bg-white overflow-y-auto">
          <div className="sticky top-0 bg-white py-4 px-6 flex items-center border-b z-10">
            <button
              type="button"
              onClick={() => setIsGalleryOpen(false)}
              className="flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium hover:bg-gray-100"
            >
              <ChevronLeft className="h-4 w-4" />
              Back to listing
            </button>
          </div>
          <div className="max-w-3xl mx-auto py-10 px-4 flex flex-col gap-4">
            {galleryImages.length ? (
              galleryImages.map((imageUrl, idx) => (
                <img
                  key={`${imageUrl}-${idx}`}
                  src={imageUrl}
                  alt={`${title} gallery ${idx + 1}`}
                  className="w-full h-auto object-cover rounded-xl"
                />
              ))
            ) : (
              <div className="w-full h-80 rounded-xl bg-gray-200 flex items-center justify-center text-gray-500">
                No photos available.
              </div>
            )}
          </div>
        </div>
      )}
      <AuthModal
        isOpen={isAuthModalOpen}
        mode="login"
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={goToCheckout}
      />
    </>
  );
}
