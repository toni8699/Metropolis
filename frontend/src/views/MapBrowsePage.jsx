import { useEffect, useMemo, useState } from "react";
import CarGrid from "@/shared/components/CarGrid";
import SearchResultsView from "@/features/browse/components/SearchResultsView";
import BodyCard from "@/shared/components/BodyCard";
import { apiGet } from "@/shared/api/api";
import { getUserLocation, haversineKm, listingCoords } from "@/shared/lib/location";
import { listingToCarCard } from "@/shared/lib/listingCard";
import { useBrowseFilters } from "@/features/browse/hooks/useBrowseFilters.jsx";
import { filtersToParams } from "@/features/browse/lib/filterParams";

export default function MapBrowsePage({ hasSearched, searchParams }) {
  const { appliedFilters, filtersActive } = useBrowseFilters();
  const [userLocation, setUserLocation] = useState(null);
  const [listings, setListings] = useState([]);
  const [totalCount, setTotalCount] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [fetchError, setFetchError] = useState("");
  const queryPath = useMemo(() => {
    const params = filtersToParams(appliedFilters, {
      searchContext: { hasSearched, searchParams },
      pagination: { limit: 100, offset: 0 },
    });
    const query = params.toString();
    return query ? `/api/listings?${query}` : "/api/listings";
  }, [appliedFilters, hasSearched, searchParams]);

  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);
    setFetchError("");

    apiGet(queryPath)
      .then((data) => {
        if (!isCancelled) {
          setListings(data?.listings || []);
          setTotalCount(Number(data?.totalCount ?? data?.listings?.length ?? 0));
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setListings([]);
          setTotalCount(0);
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
      return [];
    }

    const maxDistanceKm = 50;
    return listings.filter((listing) => {
      const coords = listingCoords(listing);
      if (!coords) return false;
      return haversineKm({ lat: center.lat, lng: center.lng }, coords) <= maxDistanceKm;
    });
  }, [hasSearched, listings, searchParams]);

  const cars = useMemo(
    () =>
      visibleListings.map((listing) => {
        const coords = listingCoords(listing);
        const hasCoords = Boolean(coords);
        return listingToCarCard(listing, {
          distanceKm: hasCoords ? haversineKm(userLocation, coords) : null,
        });
      }),
    [visibleListings, userLocation],
  );

  if (fetchError && !isLoading) {
    return <div className="neo-error text-sm font-semibold">{fetchError}</div>;
  }

  if (hasSearched) {
    return (
      <SearchResultsView
        cars={cars}
        cityLabel={searchParams?.location || visibleListings?.[0]?.cityZone || "Toronto"}
        searchCenter={searchParams?.coordinates || null}
        isLoading={isLoading}
        filtersActive={filtersActive}
        totalCount={totalCount}
      />
    );
  }

  return (
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
      ) : cars.length === 0 ? (
        <div className="relative rounded-3xl border-2 border-black bg-vroom-surface p-6 text-center shadow-neoCard">
          <p className="text-base font-extrabold text-vroom-heading">No results found</p>
          <p className="mt-2 text-sm text-vroom-muted">
            {filtersActive
              ? "Try clearing filters or widening your price range."
              : "No cars available in this area right now."}
          </p>
        </div>
      ) : (
        <CarGrid cars={cars} />
      )}
    </BodyCard>
  );
}
