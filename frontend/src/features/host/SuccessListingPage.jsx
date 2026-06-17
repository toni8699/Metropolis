import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { apiGet } from "@/shared/api/api";
import BodyCard from "@/shared/components/BodyCard";
import VroomLogo from "@/layout/VroomLogo";
import { useAuth } from "@/context/AuthContext";
import { markRecentListingCreated } from "@/features/host/lib/recentListing";

export default function SuccessListingPage() {
  const { listingId } = useParams();
  const { user, isAdmin, isAuthenticated } = useAuth();
  const [listing, setListing] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    markRecentListingCreated();
  }, []);

  useEffect(() => {
    if (!listingId) return undefined;
    let cancelled = false;

    (async () => {
      setIsLoading(true);
      setLoadError("");
      try {
        const result = await apiGet(`/api/listings/${listingId}`, true);
        if (cancelled) return;
        const nextListing = result?.listing || null;
        if (!nextListing) {
          setLoadError("Listing not found.");
          return;
        }
        setListing(nextListing);
      } catch (err) {
        if (!cancelled) {
          setLoadError(err?.message || "Could not load listing.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [listingId]);

  if (!isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  if (isAdmin) {
    return <Navigate to="/admin" replace />;
  }

  const isOwner = listing && Number(listing.ownerUserId) === Number(user?.userId);
  if (!isLoading && listing && !isOwner) {
    return <Navigate to="/host/dashboard" replace />;
  }

  const make = listing?.make || "Car";
  const model = listing?.model || "";
  const heroImage = Array.isArray(listing?.images) ? listing.images.find(Boolean) : null;
  const previewHref = `/app/listings/${listingId}`;

  return (
    <div className="min-h-screen bg-vroom-bg text-vroom-heading flex flex-col">
      <header className="flex h-20 items-center justify-between border-b-4 border-black bg-vroom-surface px-6 sm:px-10">
        <VroomLogo />
        <Link
          to="/host/dashboard"
          className="rounded-full border-2 border-black border-b-4 bg-white px-4 py-2 text-sm font-bold active:border-b-0"
        >
          Skip to dashboard
        </Link>
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-10 sm:px-6">
        {isLoading && (
          <p className="text-sm font-semibold text-vroom-muted">Loading your listing...</p>
        )}

        {!isLoading && loadError && (
          <BodyCard className="max-w-lg bg-vroom-surface rounded-2xl p-8 text-center">
            <p className="text-sm font-semibold text-vroom-errorText">{loadError}</p>
            <Link
              to="/host/dashboard"
              className="mt-6 inline-block rounded-full border-2 border-black border-b-4 bg-vroom-accent px-6 py-2.5 font-extrabold text-white active:border-b-0"
            >
              Go to My Host Dashboard
            </Link>
          </BodyCard>
        )}

        {!isLoading && listing && isOwner && (
          <div className="success-enter w-full max-w-2xl">
            <BodyCard className="bg-vroom-surface rounded-2xl p-8 sm:p-10">
              <div className="space-y-6 text-center">
                <h1 className="font-['Fredoka'] text-4xl font-extrabold text-vroom-heading leading-tight">
                  It&apos;s Official! Your {make} {model} is Live.
                </h1>

                {heroImage ? (
                  <div className="mx-auto max-w-md overflow-hidden rounded-xl border-4 border-black">
                    <img
                      src={heroImage}
                      alt={`${make} ${model}`}
                      className="aspect-[4/3] w-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="mx-auto flex aspect-[4/3] max-w-md items-center justify-center rounded-xl border-4 border-black bg-vroom-card text-sm font-semibold text-vroom-muted">
                    Photos processing...
                  </div>
                )}

                <div>
                  <span className="inline-flex rounded-full bg-vroom-sage px-4 py-1.5 text-sm font-bold text-vroom-heading">
                    Status: {listing.status || "ACTIVE"}
                  </span>
                </div>

                <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
                  <Link
                    to="/host/dashboard"
                    className="rounded-full border-2 border-black border-b-4 bg-vroom-accent px-8 py-3 font-extrabold text-white transition active:border-b-0"
                  >
                    Go to My Host Dashboard
                  </Link>
                  <a
                    href={previewHref}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-bold text-vroom-heading underline underline-offset-4 hover:text-vroom-muted"
                  >
                    Preview public listing
                  </a>
                </div>

                <div className="rounded-xl border-2 border-black bg-vroom-sage px-4 py-3 text-left text-sm font-medium text-vroom-heading">
                  Most new hosts get their first booking request within 48 hours. Keep an eye on
                  your phone!
                </div>
              </div>
            </BodyCard>
          </div>
        )}
      </main>
    </div>
  );
}
