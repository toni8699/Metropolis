import { useCallback, useState } from "react";
import { apiPost } from "@/shared/api/api";

const STATUS_LABELS = {
  succeeded: "Paid",
  pending_onboarding: "Pending setup",
  pending: "Pending",
  failed: "Failed",
  skipped: "Skipped",
};

function formatAmount(cents, currency) {
  return `${(Number(cents) / 100).toFixed(2)} ${String(currency || "CAD").toUpperCase()}`;
}

export default function PayoutsPanel({ connectStatus, recentPayouts, onRefresh }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const connect = connectStatus || {};
  const ready = Boolean(connect.ready);

  const startOnboarding = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const data = await apiPost("/api/payouts/connect/onboard", {}, true);
      const url = data?.onboardingUrl;
      if (!url) {
        throw new Error("No onboarding URL returned.");
      }
      window.location.href = url;
    } catch (err) {
      setError(err?.message || "Could not start payout setup.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <section className="mx-11 mt-6 space-y-6">
      <div className="rounded-2xl border-2 border-black bg-white p-6">
        <h2 className="text-xl font-extrabold text-vroom-heading">Payout setup</h2>
        <p className="mt-2 text-sm text-vroom-muted">
          Connect Stripe to receive earnings after each completed trip. Platform keeps the service
          fee; you receive subtotal plus cleaning fee.
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span
            className={`rounded-full px-3 py-1 text-xs font-bold ${
              ready ? "bg-green-100 text-green-900" : "bg-amber-100 text-amber-900"
            }`}
          >
            {ready ? "Payouts enabled" : "Setup required"}
          </span>
          {connect.accountId && (
            <span className="text-xs text-gray-500">Account {connect.accountId}</span>
          )}
        </div>

        {!ready && (
          <button
            type="button"
            onClick={startOnboarding}
            disabled={isLoading}
            className="mt-4 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {isLoading ? "Redirecting..." : connect.accountId ? "Continue setup" : "Set up payouts"}
          </button>
        )}

        {error && (
          <p className="mt-3 text-sm font-semibold text-red-700">{error}</p>
        )}
      </div>

      <div className="rounded-2xl border-2 border-black bg-white p-6">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-xl font-extrabold text-vroom-heading">Recent payouts</h2>
          <button
            type="button"
            onClick={onRefresh}
            className="text-sm font-semibold text-indigo-600 hover:underline"
          >
            Refresh
          </button>
        </div>

        {recentPayouts.length === 0 ? (
          <p className="mt-4 text-sm text-vroom-muted">No payouts yet. Complete a trip to get paid.</p>
        ) : (
          <ul className="mt-4 divide-y divide-gray-200">
            {recentPayouts.map((payout) => (
              <li key={payout.payoutId} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div>
                  <p className="font-semibold text-gray-900">{payout.listingTitle || "Listing"}</p>
                  <p className="text-xs text-gray-500">Booking #{payout.bookingId}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-gray-900">
                    {formatAmount(payout.amountCents, payout.currency)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {STATUS_LABELS[payout.status] || payout.status}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
