import { useState } from "react";
import { PaymentElement, useElements, useStripe } from "@stripe/react-stripe-js";

import { apiPost } from "@/shared/api/api";

export default function StripePaymentForm({ bookingId, onSuccess, onError }) {
  const stripe = useStripe();
  const elements = useElements();
  const [isPaying, setIsPaying] = useState(false);

  const handlePay = async (event) => {
    event.preventDefault();
    if (!stripe || !elements) return;
    setIsPaying(true);
    onError("");
    try {
      const { error } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/app/trips`,
        },
        redirect: "if_required",
      });
      if (error) {
        onError(error.message || "Payment failed.");
        return;
      }
      if (bookingId) {
        await apiPost(`/api/bookings/${bookingId}/payments/confirm`, {}, true);
      }
      onSuccess();
    } catch (err) {
      onError(err?.message || "Payment failed.");
    } finally {
      setIsPaying(false);
    }
  };

  return (
    <form onSubmit={handlePay} className="space-y-4">
      <PaymentElement />
      <button
        type="submit"
        disabled={!stripe || isPaying}
        className="w-full rounded-xl bg-indigo-600 px-8 py-4 text-lg font-bold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isPaying ? "Processing..." : "Pay now"}
      </button>
    </form>
  );
}
