import { useEffect, useMemo, useState } from "react";
import CarGrid from "../components/CarGrid";
import SearchResultsView from "../components/SearchResultsView";
import { apiGet } from "../utils/api";
import { getUserLocation, haversineKm } from "../lib/location";

function parseCoord(value) {
  if (value == null) return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const normalized = String(value).trim().replace(",", ".");
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

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
    return query ? `/api/market/listings?${query}` : "/api/market/listings";
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
      return listings;
    }

    const maxDistanceKm = 50;
    const nearby = listings.filter((listing) => {
      const lat = parseCoord(listing.lat);
      const lng = parseCoord(listing.lng);
      if (lat == null || lng == null) return false;
      return (
        haversineKm(
          { lat: center.lat, lng: center.lng },
          { lat, lng },
        ) <= maxDistanceKm
      );
    });

    return nearby.length > 0 ? nearby : listings;
  }, [hasSearched, listings, searchParams]);

  const cars = useMemo(
    () =>
      visibleListings.map((listing) => {
        const lat = parseCoord(listing.lat);
        const lng = parseCoord(listing.lng);
        const hasCoords = Number.isFinite(lat) && Number.isFinite(lng);
        return {
          id: listing.listingId,
          listingId: listing.listingId,
          images: listing.photos?.length ? listing.photos : [],
          image: listing.photos?.[0],
          make: listing.make || listing.brand || "",
          model: listing.model || listing.title || "",
          year: listing.year || null,
          rating: 4.9,
          details:
            listing.sourceType === "FLEET"
              ? "Company Fleet • Automatic"
              : "Host listed • Automatic",
          locationText: listing.cityZone ? `${listing.cityZone} • nearby` : null,
          pricePerDay: listing.pricePerDay,
          favorite: false,
          lat: hasCoords ? lat : null,
          lng: hasCoords ? lng : null,
          distanceKm: hasCoords
            ? haversineKm(userLocation, { lat, lng })
            : null,
        };
      }),
    [visibleListings, userLocation]
  );

  if (fetchError && !isLoading) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {fetchError}
      </div>
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
      <div className="space-y-6">
        <h2 className="text-xl font-semibold">Popular Locations and Vehicles</h2>
        {isLoading ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
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
      </div>
    )
  );
}
