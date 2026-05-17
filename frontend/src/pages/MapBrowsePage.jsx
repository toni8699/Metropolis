import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import CarGrid from "../components/CarGrid";
import SearchResultsView from "../components/SearchResultsView";
import { apiGet } from "../lib/api";
import { getUserLocation, haversineKm } from "../lib/location";

export default function MapBrowsePage({ hasSearched }) {
  const [userLocation, setUserLocation] = useState(null);

  const { data } = useQuery({
    queryKey: ["marketListings"],
    queryFn: () => apiGet("/api/market/listings?bbox=-73.75,45.45,-73.50,45.62"),
  });
  const listings = data?.listings || [];

  useEffect(() => {
    getUserLocation().then(setUserLocation);
  }, []);

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
      <SearchResultsView cars={cars} cityLabel="Montreal" />
    ) : (
      <div className="space-y-6">
        <h2 className="text-xl font-semibold">Popular Locations and Vehicles</h2>
        <CarGrid cars={cars} />
      </div>
    )
  );
}
