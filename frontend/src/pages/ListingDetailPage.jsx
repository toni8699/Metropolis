import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiGet, apiPost } from "../lib/api";

export default function ListingDetailPage() {
  const { listingId } = useParams();
  const [listing, setListing] = useState(null);
  const [bookingId, setBookingId] = useState(null);

  useEffect(() => {
    apiGet(`/api/market/listings/${listingId}`).then((data) => setListing(data.listing));
  }, [listingId]);

  const createBooking = async () => {
    const data = await apiPost(
      "/api/bookings",
      {
        listingId: Number(listingId),
        startAt: "2026-06-01T10:00:00Z",
        endAt: "2026-06-02T10:00:00Z",
      },
      true
    );
    setBookingId(data.booking?.bookingId ?? null);
  };

  if (!listing) {
    return <p>Loading listing...</p>;
  }

  return (
    <div className="space-y-4">
      <Link to="/" className="text-sm text-sky-400">
        Back to map
      </Link>
      <h1 className="text-2xl font-semibold">{listing.title}</h1>
      <p className="text-slate-300">
        {listing.brand || "Brand n/a"} • {listing.make || "Make n/a"} •{" "}
        {listing.model || "Model n/a"} {listing.year ? `(${listing.year})` : ""}
      </p>
      <p className="text-slate-300">{listing.description || "No description provided."}</p>
      <p className="text-slate-400">Price: ${listing.pricePerDay}/day</p>
      <p className="text-slate-400">Rules: {listing.rules || "No custom rules."}</p>

      <button
        onClick={createBooking}
        className="rounded bg-sky-600 px-4 py-2 font-medium hover:bg-sky-500"
      >
        Book this car
      </button>

      {bookingId && (
        <Link to={`/bookings/${bookingId}`} className="block text-sky-300">
          View booking #{bookingId}
        </Link>
      )}
    </div>
  );
}
