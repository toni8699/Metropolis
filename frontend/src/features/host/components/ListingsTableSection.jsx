import { Link } from "react-router-dom";
import { BadgeCheck, CheckCircle2, Pencil, Trash2 } from "lucide-react";
import { listingPhotos } from "@/shared/lib/listingPhotos";

const FALLBACK_PHOTO =
  "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=800&q=80";

function listingLabel(listing) {
  return (
    listing.listingTitle ||
    listing.title ||
    `${listing.make || ""} ${listing.model || ""} ${listing.year || ""}`.trim() ||
    `Listing #${listing.listingId}`
  );
}

function listingPreviewUrl(listing) {
  const { gallery } = listingPhotos(listing);
  return gallery[0] || FALLBACK_PHOTO;
}

function ListingCard({
  listing,
  showHostColumn,
  showTypeColumn,
  onEdit,
  onDelete,
}) {
  const title = listingLabel(listing);
  const specs = [listing.make, listing.model, listing.year].filter(Boolean).join(" ");
  const hasVin = Boolean(String(listing.vin || "").trim());

  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border-2 border-black bg-white shadow-neo transition hover:-translate-y-0.5">
      <Link to={`/app/listings/${listing.listingId}`} className="group block">
        <div className="relative aspect-[16/10] overflow-hidden border-b-2 border-black bg-vroom-sage">
          <img
            src={listingPreviewUrl(listing)}
            alt={title}
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
          {hasVin && (
            <span
              className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full border-2 border-black bg-white px-2.5 py-1 text-xs font-bold text-vroom-heading shadow-neo"
              title={listing.isVinVerified ? "VIN on file · Vroom verified" : "VIN on file"}
            >
              {listing.isVinVerified ? (
                <BadgeCheck className="h-4 w-4 text-emerald-600" aria-hidden />
              ) : (
                <CheckCircle2 className="h-4 w-4 text-vroom-accent" aria-hidden />
              )}
              VIN
            </span>
          )}
          <span
            className={`absolute right-3 top-3 rounded-full border-2 border-black px-2.5 py-1 text-xs font-bold ${
              listing.active ? "bg-emerald-100 text-emerald-800" : "bg-gray-100 text-gray-600"
            }`}
          >
            {listing.active ? "Active" : "Inactive"}
          </span>
        </div>
      </Link>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div>
          <Link
            to={`/app/listings/${listing.listingId}`}
            className="line-clamp-2 text-lg font-extrabold text-vroom-heading hover:underline"
          >
            {title}
          </Link>
          <p className="mt-1 text-sm font-semibold text-vroom-muted">{specs || "Specs pending"}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-vroom-muted">
          <span className="rounded-full border-2 border-black bg-vroom-surface px-3 py-1">
            ${listing.pricePerDay}/day
          </span>
          <span>
            {listing.reviewCount ?? 0} review{(listing.reviewCount ?? 0) === 1 ? "" : "s"}
            {listing.averageRating != null
              ? ` · ${Number(listing.averageRating).toFixed(1)}★`
              : ""}
          </span>
        </div>

        {(showHostColumn || showTypeColumn) && (
          <div className="flex flex-wrap gap-2 text-xs font-bold text-vroom-muted">
            {showHostColumn && (
              <span className="rounded-full border border-black/20 bg-gray-50 px-2.5 py-1">
                {listing.ownerName || `User #${listing.ownerUserId ?? "n/a"}`}
              </span>
            )}
            {showTypeColumn && (
              <span
                className={`rounded-full border-2 border-black px-2.5 py-1 ${
                  listing.isCompanyOwned
                    ? "bg-purple-100 text-purple-900"
                    : "bg-gray-100 text-gray-700"
                }`}
              >
                {listing.isCompanyOwned ? "Company" : "User"}
              </span>
            )}
          </div>
        )}

        <div className="mt-auto flex items-center gap-2 border-t-2 border-black/10 pt-3">
          <button
            type="button"
            onClick={() => onEdit(listing)}
            className="inline-flex h-9 flex-1 items-center justify-center gap-1.5 rounded-xl border-2 border-black bg-vroom-surface text-sm font-bold text-vroom-heading transition hover:bg-vroom-card"
          >
            <Pencil className="h-4 w-4" />
            Edit
          </button>
          <Link
            to={`/app/listings/${listing.listingId}`}
            className="inline-flex h-9 flex-1 items-center justify-center rounded-xl border-2 border-black border-b-4 bg-vroom-accent text-sm font-extrabold text-white transition active:border-b-2"
          >
            View
          </Link>
          <button
            type="button"
            onClick={() => onDelete(listing.listingId)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl border-2 border-black text-vroom-muted transition hover:bg-red-50 hover:text-red-600"
            aria-label="Delete listing"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </article>
  );
}

export default function ListingsTableSection({
  title,
  listings,
  showHostColumn,
  showTypeColumn,
  showAddButton = true,
  onAdd,
  onEdit,
  onDelete,
}) {
  return (
    <section className="mx-11 mt-6 mb-11">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-extrabold text-vroom-heading">{title}</h2>
        {showAddButton && (
          <button
            type="button"
            onClick={onAdd}
            className="rounded-full border-2 border-black border-b-4 bg-vroom-accent px-5 py-2 text-sm font-extrabold text-white transition active:border-b-2"
          >
            Add New Listing
          </button>
        )}
      </div>

      {listings.length === 0 ? (
        <div className="rounded-2xl border-2 border-black bg-vroom-card px-6 py-12 text-center text-sm font-semibold text-vroom-muted shadow-neo">
          No listings found.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {listings.map((listing) => (
            <ListingCard
              key={listing.listingId}
              listing={listing}
              showHostColumn={showHostColumn}
              showTypeColumn={showTypeColumn}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}
