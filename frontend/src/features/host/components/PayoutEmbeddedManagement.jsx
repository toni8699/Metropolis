import { useMemo } from "react";
import { loadConnectAndInitialize } from "@stripe/connect-js";
import {
  ConnectAccountManagement,
  ConnectComponentsProvider,
} from "@stripe/react-connect-js";
import { apiPost } from "@/shared/api/api";

const publishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || "";

export default function PayoutEmbeddedManagement({ onExit }) {
  const connectInstance = useMemo(() => {
    if (!publishableKey) {
      return null;
    }
    return loadConnectAndInitialize({
      publishableKey,
      fetchClientSecret: async () => {
        const data = await apiPost(
          "/api/payouts/connect/session",
          { component: "management" },
          true,
        );
        const secret = data?.clientSecret;
        if (!secret) {
          throw new Error("Could not open payout settings.");
        }
        return secret;
      },
      appearance: {
        variables: {
          colorPrimary: "#4f46e5",
        },
      },
    });
  }, []);

  if (!connectInstance) {
    return (
      <p className="mt-4 text-sm text-red-700">
        Stripe publishable key missing. Set VITE_STRIPE_PUBLISHABLE_KEY in frontend/.env.local.
      </p>
    );
  }

  return (
    <ConnectComponentsProvider connectInstance={connectInstance}>
      <div className="mt-4 min-h-[480px] rounded-xl border border-gray-200 bg-white p-2">
        <ConnectAccountManagement onExit={() => onExit?.()} />
      </div>
    </ConnectComponentsProvider>
  );
}
