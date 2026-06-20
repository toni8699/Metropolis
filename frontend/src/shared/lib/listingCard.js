export function listingToCarCard(listing, { distanceKm = null } = {}) {
  const transmissionLabel = listing.transmission
    ? listing.transmission === "AUTOMATIC"
      ? "Automatic"
      : listing.transmission === "MANUAL"
        ? "Manual"
        : listing.transmission
    : "Automatic";

  const lat = listing.lat ?? listing.latitude ?? null;
  const lng = listing.lng ?? listing.longitude ?? null;

  return {
    id: listing.listingId,
    listingId: listing.listingId,
    images: listing.photos?.length ? listing.photos : listing.images || [],
    image: listing.photos?.[0] || listing.images?.[0],
    make: listing.make || listing.brand || "",
    model: listing.model || listing.title || "",
    year: listing.year || null,
    averageRating: listing.averageRating,
    reviewCount: listing.reviewCount,
    details:
      listing.isCompanyOwned || listing.sourceType === "FLEET"
        ? `Company Fleet • ${transmissionLabel}`
        : `Host listed • ${transmissionLabel}`,
    locationText: listing.cityZone ? `${listing.cityZone} • nearby` : null,
    pricePerDay: Number(listing.pricePerDay ?? listing.price_per_day ?? 0),
    lat,
    lng,
    distanceKm,
  };
}
