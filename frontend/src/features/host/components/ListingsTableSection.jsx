import { Link } from "react-router-dom";
import { Pencil, Trash2 } from "lucide-react";

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
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-gray-900">{title}</h2>
        {showAddButton && (
          <button
            type="button"
            onClick={onAdd}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
          >
            Add New Listing
          </button>
        )}
      </div>
      <div className="overflow-hidden rounded-2xl border-4 border-black bg-vroom-card shadow-neo">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold tracking-wider">
              <th className="px-6 py-4">Listing</th>
              <th className="px-6 py-4">Specs</th>
              {showHostColumn && <th className="px-6 py-4">Host</th>}
              {showTypeColumn && <th className="px-6 py-4">Type</th>}
              <th className="px-6 py-4">Price</th>
              <th className="px-6 py-4">Reviews</th>
              <th className="px-6 py-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {listings.length === 0 ? (
              <tr>
                <td
                  colSpan={5 + (showHostColumn ? 1 : 0) + (showTypeColumn ? 1 : 0)}
                  className="px-6 py-8 text-sm text-gray-500 text-center"
                >
                  No listings found.
                </td>
              </tr>
            ) : (
              listings.map((listing) => (
                <tr
                  key={listing.listingId}
                  className="border-b border-gray-100 hover:bg-gray-50 transition"
                >
                  <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                    <Link
                      to={`/app/listings/${listing.listingId}`}
                      className="text-indigo-700 hover:text-indigo-900 hover:underline"
                    >
                      {listing.title}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {listing.make || "-"} {listing.model || ""}
                  </td>
                  {showHostColumn && (
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {listing.ownerName || `User #${listing.ownerUserId ?? "n/a"}`}
                    </td>
                  )}
                  {showTypeColumn && (
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          listing.isCompanyOwned
                            ? "bg-purple-100 text-purple-800"
                            : "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {listing.isCompanyOwned ? "Company" : "User"}
                      </span>
                    </td>
                  )}
                  <td className="px-6 py-4 text-sm text-gray-900">${listing.pricePerDay}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {listing.reviewCount ?? 0} review{(listing.reviewCount ?? 0) === 1 ? "" : "s"}
                    {listing.averageRating != null
                      ? ` · ${Number(listing.averageRating).toFixed(1)}★`
                      : ""}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onEdit(listing)}
                        className="h-9 w-9 rounded-lg text-gray-400 hover:text-indigo-700 hover:bg-indigo-50 transition flex items-center justify-center"
                        aria-label="Edit listing"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <Link
                        to={`/app/listings/${listing.listingId}`}
                        className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition"
                      >
                        View
                      </Link>
                      <button
                        type="button"
                        onClick={() => onDelete(listing.listingId)}
                        className="h-9 w-9 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition flex items-center justify-center"
                        aria-label="Delete listing"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
