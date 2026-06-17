import { Link } from "react-router-dom";
import { X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function VerifyEmailToast() {
  const { verifyPromptOpen, dismissVerifyEmailPrompt } = useAuth();

  if (!verifyPromptOpen) {
    return null;
  }

  return (
    <div
      role="alertdialog"
      aria-labelledby="verify-email-toast-title"
      className="fixed left-1/2 top-4 z-[70] w-[min(24rem,calc(100%-2rem))] -translate-x-1/2 rounded-2xl border-4 border-black bg-amber-50 p-4 shadow-neo"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p id="verify-email-toast-title" className="text-sm font-extrabold text-vroom-heading">
            Verify your email
          </p>
          <p className="mt-1 text-sm text-gray-700">
            We sent a verification link to your inbox. Confirm your email to unlock booking and
            hosting.
          </p>
          <Link
            to="/app/account"
            onClick={dismissVerifyEmailPrompt}
            className="mt-2 inline-block text-sm font-extrabold text-vroom-accent hover:underline"
          >
            Go to account settings
          </Link>
        </div>
        <button
          type="button"
          onClick={dismissVerifyEmailPrompt}
          className="rounded-full border-2 border-black bg-white p-1 hover:bg-vroom-sage"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
