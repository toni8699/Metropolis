import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiGet } from "@/shared/api/api";
import { useAuth } from "@/context/AuthContext";
import VroomLogo from "@/layout/VroomLogo";

const VERIFY_SUCCESS_MESSAGE =
  "Your email has been verified. You can now book trips and list your car.";

// ponytail: dedupe parallel verify calls (React StrictMode remounts same token twice)
const verifyRequests = new Map();

function verifyEmailToken(token) {
  let pending = verifyRequests.get(token);
  if (!pending) {
    pending = apiGet(`/api/auth/verify-email?token=${encodeURIComponent(token)}`).finally(() => {
      verifyRequests.delete(token);
    });
    verifyRequests.set(token, pending);
  }
  return pending;
}

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [status, setStatus] = useState("loading");
  const [message, setMessage] = useState("");
  const { refreshMe, isAuthenticated } = useAuth();
  const refreshMeRef = useRef(refreshMe);
  const isAuthenticatedRef = useRef(isAuthenticated);

  refreshMeRef.current = refreshMe;
  isAuthenticatedRef.current = isAuthenticated;

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Missing verification token.");
      return undefined;
    }

    let cancelled = false;
    (async () => {
      try {
        await verifyEmailToken(token);
        if (cancelled) return;
        if (isAuthenticatedRef.current) {
          await refreshMeRef.current();
        }
        setStatus("success");
        setMessage(VERIFY_SUCCESS_MESSAGE);
      } catch (err) {
        if (cancelled) return;
        setStatus("error");
        setMessage(err?.message || "Could not verify email.");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-vroom-bg px-4 py-10">
      <Link to="/app" className="mb-8">
        <VroomLogo />
      </Link>
      <div className="w-full max-w-md rounded-[2rem] border-4 border-black bg-vroom-surface px-8 py-10 text-center shadow-neoLg">
        {status === "loading" && (
          <>
            <h1 className="text-2xl font-extrabold text-vroom-heading">Verifying email…</h1>
            <p className="mt-3 text-sm text-gray-600">One moment.</p>
          </>
        )}
        {status === "success" && (
          <>
            <h1 className="text-2xl font-extrabold text-vroom-heading">Verification successful!</h1>
            <p className="mt-3 text-sm text-gray-600">{message}</p>
            <Link
              to={isAuthenticated ? "/app" : "/login"}
              className="neo-btn-primary mt-6 inline-block border-2 px-6 py-3 font-extrabold"
            >
              {isAuthenticated ? "Continue" : "Log in"}
            </Link>
          </>
        )}
        {status === "error" && (
          <>
            <h1 className="text-2xl font-extrabold text-vroom-heading">Verification failed</h1>
            <p className="neo-error mt-4">{message}</p>
            <Link
              to="/login"
              className="mt-6 inline-block font-extrabold text-vroom-accent hover:underline"
            >
              Back to log in
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
