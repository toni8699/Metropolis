import { useCallback, useState } from "react";
import { apiPost, getAccessToken } from "@/shared/api/api";
import PayoutEmbeddedOnboarding from "@/features/host/components/PayoutEmbeddedOnboarding";
import PayoutEmbeddedManagement from "@/features/host/components/PayoutEmbeddedManagement";

const stripePublishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || "";

const STATUS_LABELS = {
  succeeded: "Paid",
  pending_onboarding: "Payout queued",
  pending: "Pending",
  failed: "Transfer failed",
  skipped: "Skipped",
};

function formatAmount(cents, currency) {
  return `${(Number(cents) / 100).toFixed(2)} ${String(currency || "CAD").toUpperCase()}`;
}

const POLL_ATTEMPTS = 8;
const POLL_DELAY_MS = 1500;

async function pollPayoutConnectStatus(fetchStatus) {
  let latest = null;
  for (let attempt = 0; attempt < POLL_ATTEMPTS; attempt += 1) {
    latest = await fetchStatus();
    if (latest?.ready || latest?.pendingVerification) {
      return latest;
    }
    if (attempt < POLL_ATTEMPTS - 1) {
      await new Promise((resolve) => {
        setTimeout(resolve, POLL_DELAY_MS);
      });
    }
  }
  return latest;
}

export default function PayoutsPanel({ connectStatus, recentPayouts, onRefresh }) {
  const [isLoading, setIsLoading] = useState(false);
  const [showEmbedded, setShowEmbedded] = useState(false);
  const [showManagement, setShowManagement] = useState(false);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const connect = connectStatus || {};
  const ready = Boolean(connect.ready);

  const startOnboarding = useCallback(async () => {
    setError("");
    if (!stripePublishableKey) {
      setError("Stripe publishable key missing. Set VITE_STRIPE_PUBLISHABLE_KEY in frontend/.env.local.");
      return;
    }
    if (!getAccessToken()) {
      setError("Session expired. Log in again, then retry payout setup.");
      return;
    }
    setShowManagement(false);
    setShowEmbedded(true);
  }, []);

  const openManagement = useCallback(() => {
    setError("");
    if (!stripePublishableKey) {
      setError("Stripe publishable key missing. Set VITE_STRIPE_PUBLISHABLE_KEY in frontend/.env.local.");
      return;
    }
    if (!getAccessToken()) {
      setError("Session expired. Log in again, then retry payout setup.");
      return;
    }
    setShowEmbedded(false);
    setShowManagement(true);
  }, []);

  const openStripeDashboard = useCallback(async () => {
    setError("");
    if (!getAccessToken()) {
      setError("Session expired. Log in again, then retry.");
      return;
    }
    setIsLoading(true);
    try {
      const data = await apiPost("/api/payouts/connect/dashboard", {}, true);
      const url = data?.dashboardUrl;
      if (!url) {
        throw new Error("Could not open Stripe dashboard.");
      }
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err?.message || "Could not open Stripe dashboard.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleEmbeddedComplete = useCallback(async () => {
    setShowEmbedded(false);
    setError("");
    setStatusMessage("");
    if (!onRefresh) {
      return;
    }
    setIsLoading(true);
    try {
      const connect = await pollPayoutConnectStatus(onRefresh);
      if (connect?.ready) {
        setStatusMessage("Payout setup complete.");
      } else if (connect?.pendingVerification) {
        setStatusMessage("Stripe is reviewing your details. Click Refresh in a minute.");
      } else {
        setStatusMessage("Payout setup updated. Click Refresh if status looks stale.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [onRefresh]);

  const handleManagementExit = useCallback(async () => {
    setShowManagement(false);
    await onRefresh?.();
  }, [onRefresh]);

  const startOver = useCallback(async () => {
    if (!window.confirm("Unlink Stripe payout account and start setup from scratch?")) {
      return;
    }
    setError("");
    setShowEmbedded(false);
    setShowManagement(false);
    setIsLoading(true);
    try {
      await apiPost("/api/payouts/connect/reset", {}, true);
      await onRefresh?.();
      await startOnboarding();
    } catch (err) {
      setError(err?.message || "Could not reset payout setup.");
    } finally {
      setIsLoading(false);
    }
  }, [onRefresh, startOnboarding]);

  return (
    <section className="mx-11 mt-6 space-y-6">
      <div className="rounded-2xl border-2 border-black bg-white p-6">
        <h2 className="text-xl font-extrabold text-vroom-heading">Payout setup</h2>
        <p className="mt-2 text-sm text-vroom-muted">
          Connect Stripe to receive earnings after each completed trip. Platform keeps the service
          fee; you receive subtotal plus cleaning fee. Business details are prefilled from Vroom.
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

        {!stripePublishableKey && (
          <p className="mt-4 text-sm font-semibold text-red-700">
            Set VITE_STRIPE_PUBLISHABLE_KEY in frontend/.env.local to use embedded payout setup.
          </p>
        )}

        {!ready && !showEmbedded && stripePublishableKey && (
          <button
            type="button"
            onClick={startOnboarding}
            disabled={isLoading}
            className="mt-4 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {isLoading ? "Checking status..." : connect.accountId ? "Continue setup" : "Set up payouts"}
          </button>
        )}

        {ready && !showManagement && (
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={openManagement}
              disabled={isLoading}
              className="rounded-xl border-2 border-indigo-600 px-5 py-2.5 text-sm font-bold text-indigo-700 hover:bg-indigo-50 disabled:opacity-50"
            >
              Manage payout settings
            </button>
            <button
              type="button"
              onClick={openStripeDashboard}
              disabled={isLoading}
              className="text-sm font-semibold text-indigo-600 underline hover:text-indigo-800 disabled:opacity-50"
            >
              {isLoading ? "Opening..." : "Open Stripe Express dashboard"}
            </button>
          </div>
        )}

        {showEmbedded && (
          <PayoutEmbeddedOnboarding onComplete={handleEmbeddedComplete} />
        )}

        {showManagement && (
          <PayoutEmbeddedManagement onExit={handleManagementExit} />
        )}

        {import.meta.env.DEV && connect.accountId && (
          <button
            type="button"
            onClick={startOver}
            disabled={isLoading}
            className="mt-3 block text-sm font-semibold text-gray-500 underline hover:text-gray-700 disabled:opacity-50"
          >
            Start over (dev)
          </button>
        )}

        {connect.pendingVerification && (
          <p className="mt-3 text-sm text-vroom-muted">
            Stripe is reviewing your details. Click Refresh in a minute.
          </p>
        )}

        {!ready && connect.onboardingRequired && !connect.pendingVerification && !showEmbedded && (
          <p className="mt-3 text-sm text-vroom-muted">
            Complete bank and identity steps below to enable payouts.
          </p>
        )}

        {ready && recentPayouts.some((p) => p.status === "pending_onboarding" || p.status === "failed") && (
          <p className="mt-3 text-sm text-vroom-muted">
            Stripe is connected. Click Refresh to retry queued or failed trip payouts.
          </p>
        )}

        {statusMessage && (
          <p className="mt-3 text-sm font-semibold text-green-800">{statusMessage}</p>
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
