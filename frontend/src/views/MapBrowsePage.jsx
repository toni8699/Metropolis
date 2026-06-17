import { useEffect, useMemo, useState } from "react";
import CarGrid from "@/shared/components/CarGrid";
import SearchResultsView from "@/features/browse/components/SearchResultsView";
import BodyCard from "@/shared/components/BodyCard";
import { apiGet } from "@/shared/api/api";
import { getUserLocation, haversineKm, listingCoords } from "@/shared/lib/location";

export default function MapBrowsePage({ hasSearched, searchParams }) {
  const [userLocation, setUserLocation] = useState(null);
  const [listings, setListings] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [fetchError, setFetchError] = useState("");

  const queryPath = useMemo(() => {
    const params = new URLSearchParams();
    if (!hasSearched) {
      params.set("bbox", "-79.65,43.58,-79.10,43.86");
    }
    if (searchParams?.pickupDate) {
      params.set("start", `${searchParams.pickupDate}T00:00:00Z`);
    }
    if (searchParams?.returnDate) {
      params.set("end", `${searchParams.returnDate}T00:00:00Z`);
    }
    if (searchParams?.coordinates?.lat != null && searchParams?.coordinates?.lng != null) {
      params.set("lat", String(searchParams.coordinates.lat));
      params.set("lng", String(searchParams.coordinates.lng));
      params.set("radius", "50");
    }
    const query = params.toString();
    return query ? `/api/listings?${query}` : "/api/listings";
  }, [hasSearched, searchParams]);

  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);
    setFetchError("");

    apiGet(queryPath)
      .then((data) => {
        if (!isCancelled) {
          setListings(data?.listings || []);
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setListings([]);
          setFetchError(err?.message || "Could not load listings.");
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [queryPath]);

  useEffect(() => {
    getUserLocation().then(setUserLocation);
  }, []);

  const visibleListings = useMemo(() => {
    if (!hasSearched) return listings;

    const center = searchParams?.coordinates;
    if (center?.lat == null || center?.lng == null) {
      // Search without resolved coordinates — don't show unrelated city inventory.
      return [];
    }

    const maxDistanceKm = 50;
    return listings.filter((listing) => {
      const coords = listingCoords(listing);
      if (!coords) return false;
      return (
        haversineKm(
          { lat: center.lat, lng: center.lng },
          coords,
        ) <= maxDistanceKm
      );
    });
  }, [hasSearched, listings, searchParams]);

  const cars = useMemo(
    () =>
      visibleListings.map((listing) => {
        const coords = listingCoords(listing);
        const hasCoords = Boolean(coords);
        return {
          id: listing.listingId,
          listingId: listing.listingId,
          images: listing.photos?.length ? listing.photos : [],
          image: listing.photos?.[0],
          make: listing.make || listing.brand || "",
          model: listing.model || listing.title || "",
          year: listing.year || null,
          averageRating: listing.averageRating,
          reviewCount: listing.reviewCount,
          details:
            listing.isCompanyOwned || listing.sourceType === "FLEET"
              ? "Company Fleet • Automatic"
              : "Host listed • Automatic",
          locationText: listing.cityZone ? `${listing.cityZone} • nearby` : null,
          pricePerDay: Number(listing.pricePerDay ?? listing.price_per_day ?? 0),
          favorite: false,
          lat: hasCoords ? coords.lat : null,
          lng: hasCoords ? coords.lng : null,
          distanceKm: hasCoords
            ? haversineKm(userLocation, coords)
            : null,
        };
      }),
    [visibleListings, userLocation]
  );

  if (fetchError && !isLoading) {
    return (
      <div className="neo-error text-sm font-semibold">{fetchError}</div>
    );
  }

  return (
    hasSearched ? (
      <SearchResultsView
        cars={cars}
        cityLabel={searchParams?.location || visibleListings?.[0]?.cityZone || "Toronto"}
        searchCenter={searchParams?.coordinates || null}
        isLoading={isLoading}
      />
    ) : (
      <BodyCard className="relative space-y-5 overflow-hidden px-6 py-6">
        <div className="pointer-events-none absolute -left-12 -top-12 h-28 w-28 rounded-full bg-vroom-accent/20" />
        <div className="pointer-events-none absolute -bottom-10 right-10 h-24 w-24 rounded-full bg-vroom-heading/15" />
        <h2 className="relative text-2xl font-extrabold text-vroom-heading">
          Popular Locations and Vehicles
        </h2>
        {isLoading ? (
          <div className="relative grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, idx) => (
              <div key={idx} className="space-y-3">
                <div className="aspect-[20/19] animate-pulse rounded-2xl bg-gray-200" />
                <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
                <div className="h-4 w-1/2 animate-pulse rounded bg-gray-100" />
              </div>
            ))}
          </div>
        ) : (
          <CarGrid cars={cars} />
        )}
      </BodyCard>
    )
  );
}
