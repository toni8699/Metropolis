import { useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function formatDate(value) {
  if (!value) return "Not available";
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(new Date(value));
  } catch {
    return "Not available";
  }
}

export default function AccountSettingsPage() {
  const { isAuthenticated, user, updateProfile } = useAuth();
  const [form, setForm] = useState({ fullName: "", phone: "" });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    setForm({
      fullName: user?.fullName || "",
      phone: user?.phone || "",
    });
  }, [user?.fullName, user?.phone]);

  const hasChanges = useMemo(() => {
    return (
      form.fullName !== (user?.fullName || "") ||
      form.phone !== (user?.phone || "")
    );
  }, [form.fullName, form.phone, user?.fullName, user?.phone]);

  if (!isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setIsSaving(true);
    try {
      await updateProfile({
        fullName: form.fullName,
        phone: form.phone,
      });
      setSuccess("Profile updated.");
    } catch (err) {
      setError(err?.message || "Could not update your profile.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900">Account settings</h1>
        <p className="mt-2 text-gray-600">
          Manage the identity details DriveBnb uses across bookings, messages, and hosting.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
      >
        <div className="grid gap-5">
          <div>
            <label className="block text-sm font-semibold text-gray-900" htmlFor="fullName">
              Full name
            </label>
            <input
              id="fullName"
              type="text"
              maxLength={150}
              value={form.fullName}
              onChange={(event) =>
                setForm((current) => ({ ...current, fullName: event.target.value }))
              }
              placeholder="Add your name"
              className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-indigo-600"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-900" htmlFor="phone">
              Phone
            </label>
            <input
              id="phone"
              type="tel"
              maxLength={32}
              value={form.phone}
              onChange={(event) =>
                setForm((current) => ({ ...current, phone: event.target.value }))
              }
              placeholder="Add your phone number"
              className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-indigo-600"
            />
            <p className="mt-2 text-xs text-gray-500">
              Phone is private and used for account and trip coordination.
            </p>
          </div>

          <div className="grid gap-4 rounded-xl bg-gray-50 p-4 text-sm text-gray-700 sm:grid-cols-3">
            <div>
              <p className="font-semibold text-gray-900">Email</p>
              <p className="mt-1 break-words">{user?.email}</p>
            </div>
            <div>
              <p className="font-semibold text-gray-900">Role</p>
              <p className="mt-1 capitalize">{user?.role || "user"}</p>
            </div>
            <div>
              <p className="font-semibold text-gray-900">Member since</p>
              <p className="mt-1">{formatDate(user?.createdAt)}</p>
            </div>
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700">
              {success}
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!hasChanges || isSaving}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isSaving ? "Saving..." : "Save changes"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
