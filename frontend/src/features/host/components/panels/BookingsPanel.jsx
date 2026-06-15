import { useMemo } from "react";
import { Link } from "react-router-dom";
import {
  bookingStatusBadgeClass,
  formatBookingStatusLabel,
  isPendingApproval,
} from "@/shared/lib/bookingStatus";
import { formatBookingWindow } from "@/features/host/lib/dashboardAnalytics";

export default function BookingsPanel({ isAdmin, bookings, bookingActionId, onDecision }) {
  const pendingApprovalBookings = useMemo(
    () => bookings.filter((booking) => isPendingApproval(booking.status)),
    [bookings],
  );

  return (
    <div className="mx-11 mt-6 mb-11 space-y-6">
      {!isAdmin && pendingApprovalBookings.length > 0 && (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-lg font-semibold text-amber-950">Awaiting your approval</h3>
              <p className="mt-1 text-sm text-amber-900/80">
                {pendingApprovalBookings.length} booking
                {pendingApprovalBookings.length === 1 ? "" : "s"} need a decision.
              </p>
            </div>
            <span className="rounded-full bg-amber-200 px-3 py-1 text-xs font-semibold text-amber-950">
              {pendingApprovalBookings.length} pending
            </span>
          </div>
          <div className="space-y-3">
            {pendingApprovalBookings.map((booking) => (
              <div
                key={booking.bookingId}
                className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-amber-200 bg-white p-4"
              >
                <div>
                  <p className="font-semibold text-gray-900">
                    #{booking.bookingId} · {booking.listingTitle || "Listing"}
                  </p>
                  <p className="mt-1 text-sm text-gray-600">
                    {booking.renterEmail || `Renter #${booking.renterUserId || "n/a"}`} ·{" "}
                    {formatBookingWindow(booking.startAt, booking.endAt)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={bookingActionId === booking.bookingId}
                    onClick={() => onDecision(booking.bookingId, "reject")}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    disabled={bookingActionId === booking.bookingId}
                    onClick={() => onDecision(booking.bookingId, "approve")}
                    className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white hover:bg-black disabled:opacity-50"
                  >
                    {bookingActionId === booking.bookingId ? "Saving..." : "Approve"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="overflow-hidden rounded-2xl border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 text-xs font-semibold uppercase tracking-wider text-gray-500">
              <th className="px-6 py-4">Booking</th>
              <th className="px-6 py-4">Listing</th>
              <th className="px-6 py-4">Window</th>
              <th className="px-6 py-4">Status</th>
              {!isAdmin && <th className="px-6 py-4">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {bookings.length === 0 ? (
              <tr>
                <td
                  colSpan={isAdmin ? 4 : 5}
                  className="px-6 py-10 text-center text-sm text-gray-500"
                >
                  No bookings yet.
                </td>
              </tr>
            ) : (
              bookings.map((booking) => {
                const pending = isPendingApproval(booking.status);
                return (
                  <tr
                    key={booking.bookingId}
                    className={`border-b border-gray-100 transition hover:bg-gray-50 ${
                      pending ? "bg-amber-50/40" : ""
                    }`}
                  >
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      <Link
                        to={`/app/bookings/${booking.bookingId}`}
                        className="font-semibold text-indigo-600 hover:text-indigo-800 hover:underline"
                      >
                        #{booking.bookingId}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">{booking.listingTitle}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatBookingWindow(booking.startAt, booking.endAt)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${bookingStatusBadgeClass(booking.status)}`}
                      >
                        {formatBookingStatusLabel(booking.status)}
                      </span>
                    </td>
                    {!isAdmin && (
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {pending ? (
                          <div className="flex flex-wrap gap-2">
                            <button
                              type="button"
                              disabled={bookingActionId === booking.bookingId}
                              onClick={() => onDecision(booking.bookingId, "reject")}
                              className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                            >
                              Reject
                            </button>
                            <button
                              type="button"
                              disabled={bookingActionId === booking.bookingId}
                              onClick={() => onDecision(booking.bookingId, "approve")}
                              className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-black disabled:opacity-50"
                            >
                              Approve
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
