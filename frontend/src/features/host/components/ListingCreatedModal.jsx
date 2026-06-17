export default function ListingCreatedModal({ listing, listingsTabId, onViewListings, onPreview }) {
  if (!listing) return null;

  const previewHref = `/app/listings/${listing.listingId}`;

  return (
    <div
      className="modal-enter fixed inset-0 z-[70] flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="listing-created-title"
    >
      <div className="w-full max-w-md rounded-2xl border-4 border-black bg-vroom-surface p-8 shadow-neo">
        <h2
          id="listing-created-title"
          className="font-['Fredoka'] text-2xl font-extrabold text-vroom-heading text-center"
        >
          🎉 Your car is ready for the road!
        </h2>

        <div className="mt-6 rounded-xl border-4 border-black bg-vroom-heading px-4 py-3 text-center">
          <p className="font-extrabold text-white text-lg">{listing.title}</p>
          <p className="mt-1 text-vroom-sage font-bold text-xl">
            ${Number(listing.pricePerDay).toFixed(0)}/day
          </p>
        </div>

        <div className="mt-8 flex flex-col gap-3">
          <button
            type="button"
            onClick={() => onViewListings(listingsTabId)}
            className="w-full rounded-full border-2 border-black border-b-4 bg-vroom-accent px-6 py-3 font-extrabold text-white transition-all hover:translate-y-[-2px] active:translate-y-0 active:border-b-2"
          >
            View My Listings
          </button>
          <a
            href={previewHref}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onPreview}
            className="w-full text-center text-sm font-bold text-vroom-heading underline underline-offset-4 hover:text-vroom-muted"
          >
            Preview Public Page
          </a>
        </div>
      </div>
    </div>
  );
}
