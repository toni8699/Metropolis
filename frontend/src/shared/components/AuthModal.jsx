import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const googleClientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID || "";

export default function AuthModal({ isOpen, mode = "login", onClose, onSuccess }) {
  const [authMode, setAuthMode] = useState(mode);
  const [form, setForm] = useState({ email: "", password: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const { login, register, googleLogin } = useAuth();
  const googleButtonRef = useRef(null);

  useEffect(() => {
    setAuthMode(mode);
  }, [mode, isOpen]);

  useEffect(() => {
    if (!isOpen || !googleClientId || !googleButtonRef.current) return undefined;
    const mountGoogle = () => {
      if (!window.google?.accounts?.id || !googleButtonRef.current) return;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response) => {
          setError("");
          setIsLoading(true);
          try {
            await googleLogin(response.credential);
            onClose?.();
            onSuccess?.();
          } catch (err) {
            setError(err?.message || "Google sign-in failed.");
          } finally {
            setIsLoading(false);
          }
        },
      });
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: "outline",
        size: "large",
        width: 320,
      });
    };
    if (window.google?.accounts?.id) {
      mountGoogle();
      return undefined;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = mountGoogle;
    document.body.appendChild(script);
    return () => {
      script.remove();
    };
  }, [isOpen, googleLogin, onClose, onSuccess]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const onEsc = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const submitLabel = authMode === "login" ? "Log in" : "Sign up";

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      if (authMode === "login") {
        await login(form.email, form.password);
      } else {
        await register({ ...form });
      }
      onClose?.();
      onSuccess?.();
    } catch (err) {
      setError(err?.message || "Could not authenticate. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="modal-enter fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4"
      onClick={() => onClose?.()}
    >
      <div
        className="relative w-full max-w-md overflow-hidden rounded-[2rem] border-4 border-black bg-vroom-surface shadow-neoLg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="relative border-b-2 border-black pb-4 pt-4">
          <button
            onClick={() => onClose?.()}
            className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full border-2 border-black bg-white p-2 hover:scale-105"
            aria-label="Close auth modal"
          >
            <X className="h-4 w-4" />
          </button>
          <p className="text-center text-sm font-extrabold text-vroom-heading">Log in or sign up</p>
        </div>

        <div className="px-6 pb-6">
          <h2 className="mb-6 mt-4 text-3xl font-extrabold text-vroom-heading">Welcome to VROOM</h2>
          <form className="space-y-3" onSubmit={handleSubmit}>
            {error && (
              <div className="neo-error mb-4">{error}</div>
            )}
            <input
              type="email"
              required
              value={form.email}
              onChange={(event) =>
                setForm((current) => ({ ...current, email: event.target.value }))
              }
              className="neo-input"
              placeholder="Email"
            />
            <input
              type="password"
              required
              value={form.password}
              onChange={(event) =>
                setForm((current) => ({ ...current, password: event.target.value }))
              }
              placeholder="Password"
              className="neo-input"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="neo-btn-primary mt-4 w-full border-2 py-3"
            >
              {isLoading
                ? authMode === "login"
                  ? "Logging in..."
                  : "Signing up..."
                : submitLabel}
            </button>
          </form>

          <div className="mt-4 flex min-h-[44px] flex-col items-center justify-center">
            {googleClientId ? (
              <div ref={googleButtonRef} />
            ) : (
              <p className="text-center text-sm text-amber-600">
                Google sign-in: set VITE_GOOGLE_OAUTH_CLIENT_ID in frontend/.env.local
              </p>
            )}
          </div>

          <p className="mt-4 text-center text-sm text-gray-600">
            {authMode === "login" ? "New to VROOM?" : "Already have an account?"}{" "}
            <button
              onClick={() =>
                setAuthMode((current) => (current === "login" ? "signup" : "login"))
              }
              className="font-extrabold text-vroom-accent hover:underline"
            >
              {authMode === "login" ? "Sign up" : "Log in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
