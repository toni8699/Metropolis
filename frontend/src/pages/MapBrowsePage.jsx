import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import CarGrid from "../components/CarGrid";
import SearchResultsView from "../components/SearchResultsView";
import { apiGet } from "../lib/api";
import { getUserLocation, haversineKm } from "../lib/location";

export default function MapBrowsePage({ hasSearched, searchParams }) {
  const [userLocation, setUserLocation] = useState(null);

  const queryPath = useMemo(() => {
    if (!hasSearched) {
      return "/api/market/listings?bbox=-73.75,45.45,-73.50,45.62";
    }
    const params = new URLSearchParams();
    if (searchParams?.pickupDate) {
      params.set("start", `${searchParams.pickupDate}T00:00:00Z`);
    }
    if (searchParams?.returnDate) {
      params.set("end", `${searchParams.returnDate}T00:00:00Z`);
    }
    const query = params.toString();
    return query ? `/api/market/listings?${query}` : "/api/market/listings";
  }, [hasSearched, searchParams]);

  const { data } = useQuery({
    queryKey: ["marketListings", queryPath],
    queryFn: () => apiGet(queryPath),
  });
  const rawListings = data?.listings || [];

  useEffect(() => {
    getUserLocation().then(setUserLocation);
  }, []);

  const listings = useMemo(() => {
    if (!hasSearched) return rawListings;

    const center = searchParams?.coordinates;
    if (center?.lat == null || center?.lng == null) {
      return rawListings;
    }

    const maxDistanceKm = 80;
    const nearby = rawListings.filter((listing) => {
      if (listing.lat == null || listing.lng == null) return false;
      return (
        haversineKm(
          { lat: center.lat, lng: center.lng },
          { lat: listing.lat, lng: listing.lng },
        ) <= maxDistanceKm
      );
    });

    return nearby.length > 0 ? nearby : rawListings;
  }, [hasSearched, rawListings, searchParams]);

  const cars = useMemo(
    () =>
      listings.map((listing) => ({
        id: listing.listingId,
        listingId: listing.listingId,
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
        lat: listing.lat,
        lng: listing.lng,
        distanceKm:
          listing.lat != null && listing.lng != null
            ? haversineKm(userLocation, { lat: listing.lat, lng: listing.lng })
            : null,
      })),
    [listings, userLocation]
  );

  return (
    hasSearched ? (
      <SearchResultsView
        cars={cars}
        cityLabel={searchParams?.location || listings?.[0]?.cityZone || "Montreal"}
        searchCenter={searchParams?.coordinates || null}
      />
    ) : (
      <div className="space-y-6">
        <h2 className="text-xl font-semibold">Popular Locations and Vehicles</h2>
        <CarGrid cars={cars} />
      </div>
    )
  );
}
