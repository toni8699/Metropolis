import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useSavedListings } from "@/context/SavedListingsContext";
import CarGrid from "@/shared/components/CarGrid";
import PageShell from "@/shared/components/PageShell";
import { apiGet } from "@/shared/api/api";
import { listingToCarCard } from "@/shared/lib/listingCard";

export default function SavedListingsPage() {
  const { isAuthenticated } = useAuth();
  const { refreshSaved } = useSavedListings();
  const [listings, setListings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadSaved = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const data = await apiGet("/api/me/saved-listings", true);
      setListings(data?.listings || []);
      await refreshSaved();
    } catch (err) {
      setListings([]);
      setError(err?.message || "Could not load saved listings.");
    } finally {
      setIsLoading(false);
    }
  }, [refreshSaved]);

  useEffect(() => {
    if (!isAuthenticated) return;
    loadSaved();
  }, [isAuthenticated, loadSaved]);

  const cars = useMemo(
    () => listings.map((listing) => listingToCarCard(listing)),
    [listings],
  );

  if (!isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  return (
    <PageShell maxWidth="7xl" card className="space-y-6 p-6">
      <div>
        <h1 className="text-4xl font-extrabold text-vroom-heading">Saved listings</h1>
        <p className="mt-2 text-vroom-muted">Cars you hearted while browsing.</p>
      </div>

      {error && (
        <div className="rounded-xl border-2 border-black bg-vroom-error px-4 py-3 text-sm font-semibold text-vroom-errorText">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="space-y-3">
              <div className="aspect-[4/3] animate-pulse rounded-2xl bg-gray-200" />
              <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-gray-100" />
            </div>
          ))}
        </div>
      ) : cars.length === 0 ? (
        <div className="rounded-3xl border-2 border-black bg-vroom-surface p-8 text-center shadow-neoCard">
          <p className="font-semibold text-vroom-muted">No saved listings yet.</p>
          <Link
            to="/app"
            className="mt-4 inline-block rounded-full border-2 border-black border-b-4 bg-vroom-accent px-5 py-2.5 font-extrabold text-white active:border-b-0"
          >
            Browse cars
          </Link>
        </div>
      ) : (
        <CarGrid cars={cars} />
      )}
    </PageShell>
  );
}
