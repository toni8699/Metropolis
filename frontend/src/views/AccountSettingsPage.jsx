import { useEffect, useMemo, useRef, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import UserAvatar from "@/shared/components/UserAvatar";
import { useAuth } from "@/context/AuthContext";
import { uploadProfilePhoto } from "@/shared/lib/uploadProfilePhoto";

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
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const photoInputRef = useRef(null);

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
    return <Navigate to="/login?redirect_to=/app/account" replace />;
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

  const handlePhotoChange = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Choose an image file.");
      setSuccess("");
      return;
    }

    setError("");
    setSuccess("");
    setIsUploadingPhoto(true);
    try {
      const fileUrl = await uploadProfilePhoto(file);
      await updateProfile({ profilePhotoUrl: fileUrl });
      setSuccess("Profile photo updated.");
    } catch (err) {
      setError(err?.message || "Could not upload profile photo.");
    } finally {
      setIsUploadingPhoto(false);
    }
  };

  const handleRemovePhoto = async () => {
    setError("");
    setSuccess("");
    setIsUploadingPhoto(true);
    try {
      await updateProfile({ profilePhotoUrl: null });
      setSuccess("Profile photo removed.");
    } catch (err) {
      setError(err?.message || "Could not remove profile photo.");
    } finally {
      setIsUploadingPhoto(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500">
        <Link to="/" className="hover:text-gray-700">
          Home
        </Link>
        <span className="mx-2">›</span>
        <span className="text-gray-700">Account Settings</span>
      </nav>
      <div>
        <h1 className="text-3xl font-semibold text-gray-900">Account settings</h1>
        <p className="mt-2 text-gray-600">
          Manage the identity details DriveBnb uses across bookings, messages, and hosting.
        </p>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <UserAvatar user={user} className="h-16 w-16 text-lg" />
            <div>
              <p className="text-sm font-semibold text-gray-900">Profile photo</p>
              <p className="mt-1 text-sm text-gray-600">
                Shown in the header. Without a photo, your initials appear instead.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <input
              ref={photoInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handlePhotoChange}
            />
            <button
              type="button"
              disabled={isUploadingPhoto}
              onClick={() => photoInputRef.current?.click()}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isUploadingPhoto ? "Uploading..." : user?.profilePhotoUrl ? "Change photo" : "Add photo"}
            </button>
            {user?.profilePhotoUrl && (
              <button
                type="button"
                disabled={isUploadingPhoto}
                onClick={handleRemovePhoto}
                className="rounded-lg px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Remove
              </button>
            )}
          </div>
        </div>
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
