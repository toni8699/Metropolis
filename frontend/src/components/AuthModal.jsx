import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function AuthModal({ isOpen, mode = "login", onClose, onSuccess }) {
  const [authMode, setAuthMode] = useState(mode);
  const [form, setForm] = useState({ email: "", password: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const { login, register } = useAuth();

  useEffect(() => {
    setAuthMode(mode);
  }, [mode, isOpen]);

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
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4"
      onClick={() => onClose?.()}
    >
      <div
        className="relative w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="relative border-b pb-4 pt-4">
          <button
            onClick={() => onClose?.()}
            className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full p-2 hover:bg-gray-100"
            aria-label="Close auth modal"
          >
            <X className="h-4 w-4" />
          </button>
          <p className="text-center text-sm font-bold">Log in or sign up</p>
        </div>

        <div className="px-6 pb-6">
          <h2 className="mb-6 mt-4 text-2xl font-semibold">Welcome to DriveBnb</h2>
          <form className="space-y-3" onSubmit={handleSubmit}>
            {error && (
              <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}
            <input
              type="email"
              required
              value={form.email}
              onChange={(event) =>
                setForm((current) => ({ ...current, email: event.target.value }))
              }
              placeholder="Email"
              className="w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-black"
            />
            <input
              type="password"
              required
              value={form.password}
              onChange={(event) =>
                setForm((current) => ({ ...current, password: event.target.value }))
              }
              placeholder="Password"
              className="w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-black"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="mt-4 w-full rounded-lg bg-indigo-600 py-3 font-bold text-white disabled:opacity-40"
            >
              {isLoading
                ? authMode === "login"
                  ? "Logging in..."
                  : "Signing up..."
                : submitLabel}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-600">
            {authMode === "login" ? "New to DriveBnb?" : "Already have an account?"}{" "}
            <button
              onClick={() =>
                setAuthMode((current) => (current === "login" ? "signup" : "login"))
              }
              className="font-medium text-indigo-600 hover:underline"
            >
              {authMode === "login" ? "Sign up" : "Log in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
