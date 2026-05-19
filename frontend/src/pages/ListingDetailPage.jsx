import { useEffect, useMemo, useState } from "react";
import { CarFront, Fuel, Settings, Star, UserCircle2 } from "lucide-react";
import { useParams } from "react-router-dom";
import { apiGet } from "../utils/api";

export default function ListingDetailPage() {
  const { listingId } = useParams();
  const [listing, setListing] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

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

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-10">
        <div className="space-y-4">
          <div className="h-10 w-2/3 animate-pulse rounded bg-gray-200" />
          <div className="h-5 w-1/3 animate-pulse rounded bg-gray-100" />
          <div className="grid h-[50vh] grid-cols-4 grid-rows-2 gap-2 overflow-hidden rounded-2xl md:h-[60vh]">
            {Array.from({ length: 5 }).map((_, idx) => (
              <div
                key={idx}
                className={`animate-pulse bg-gray-200 ${
                  idx === 0 ? "col-span-2 row-span-2" : "col-span-1 row-span-1"
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
  const reviews = 42;
  const rating = 4.92;
  const locationText = listing.cityZone ? listing.cityZone.replace(/-/g, " ") : "Location";

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-10">
      <h1 className="mb-2 text-3xl font-semibold text-gray-900">{title}</h1>
      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
        <span className="flex items-center gap-1 underline">
          <Star className="h-4 w-4 fill-current" />
          {rating.toFixed(2)}
        </span>
        <span>·</span>
        <span className="underline">{reviews} reviews</span>
        <span>·</span>
        <span className="underline">{locationText}</span>
      </div>

      <div className="group relative mt-6 grid h-[50vh] grid-cols-4 grid-rows-2 gap-2 overflow-hidden rounded-2xl md:h-[60vh]">
        {[0, 1, 2, 3, 4].map((index) => (
          <div
            key={index}
            className={`${index === 0 ? "col-span-2 row-span-2" : "col-span-1 row-span-1"} overflow-hidden`}
          >
            {images[index] ? (
              <img
                src={images[index]}
                alt={`${title} photo ${index + 1}`}
                className="h-full w-full cursor-pointer object-cover transition hover:opacity-90"
              />
            ) : (
              <div className="h-full w-full bg-gray-200" />
            )}
          </div>
        ))}
        <button className="absolute bottom-4 right-4 flex items-center gap-2 rounded-lg border border-black bg-white px-4 py-1.5 text-sm font-semibold shadow-md transition hover:bg-gray-50">
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
                Hosted by {listing.ownerName || "DriveBnb Host"}
              </p>
              <p className="text-sm text-gray-500">
                {listing.sourceType === "FLEET" ? "Fleet manager" : "Individual host"}
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

          <div className="grid gap-3 sm:grid-cols-2">
            {[
              "Instant booking",
              "Free cancellation in 24h",
              "Apple CarPlay",
              "Bluetooth audio",
              "Backup camera",
              "Unlimited support",
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-2 text-sm text-gray-800">
                <span className="h-1.5 w-1.5 rounded-full bg-gray-900" />
                {feature}
              </div>
            ))}
          </div>
        </div>

        <div className="w-full md:w-[35%]">
          <div className="sticky top-28 rounded-2xl border border-gray-200 bg-white p-6 shadow-xl">
            <div className="flex items-baseline gap-1">
              <p className="text-2xl font-bold text-gray-900">${listing.pricePerDay}</p>
              <p className="text-gray-600">/ day</p>
            </div>

            <div className="mt-4 rounded-xl border border-gray-300">
              <div className="grid grid-cols-2">
                <div className="border-r p-3">
                  <p className="text-xs font-semibold uppercase text-gray-500">Check-in</p>
                  <p className="text-sm text-gray-700">Add date</p>
                </div>
                <div className="p-3">
                  <p className="text-xs font-semibold uppercase text-gray-500">Checkout</p>
                  <p className="text-sm text-gray-700">Add date</p>
                </div>
              </div>
            </div>

            <button className="mt-4 w-full rounded-lg bg-indigo-600 py-3 font-bold text-white transition hover:bg-indigo-700">
              Reserve
            </button>
            <p className="mt-3 text-center text-sm text-gray-500">
              You won&apos;t be charged yet
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
