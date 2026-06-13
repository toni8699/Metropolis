import { useEffect, useMemo, useRef, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { CheckCircle2, Circle, Loader2, Star } from "lucide-react";
import AvatarCropModal from "@/shared/components/AvatarCropModal";
import UserAvatar from "@/shared/components/UserAvatar";
import { useAuth } from "@/context/AuthContext";
import { uploadProfilePhoto } from "@/shared/lib/uploadProfilePhoto";

const fieldLabelClass =
  "mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-400";
const fieldInputClass =
  "w-full rounded-lg border border-gray-300 px-4 py-3 text-sm text-gray-900 outline-none transition focus:border-indigo-600";

function firstName(fullName) {
  const trimmed = String(fullName || "").trim();
  return trimmed.split(/\s+/)[0] || "Guest";
}

function VerifiedRow({ label, verified, action }) {
  return (
    <div className="flex items-center justify-between border-b border-gray-100 py-3 last:border-b-0">
      <div>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {!verified && action}
      </div>
      {verified ? (
        <CheckCircle2 className="h-5 w-5 shrink-0 text-indigo-600" aria-hidden="true" />
      ) : (
        <Circle className="h-5 w-5 shrink-0 text-gray-300" aria-hidden="true" />
      )}
    </div>
  );
}

export default function AccountSettingsPage() {
  const { isAuthenticated, user, updateProfile } = useAuth();
  const [form, setForm] = useState({
    lives: "",
    about: "",
    languages: "",
    work: "",
    phone: "",
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);
  const [cropImageSrc, setCropImageSrc] = useState(null);
  const [isCropModalOpen, setIsCropModalOpen] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const photoInputRef = useRef(null);
  const phoneInputRef = useRef(null);

  useEffect(() => {
    setForm({
      lives: user?.lives || "",
      about: user?.about || "",
      languages: user?.languages || "",
      work: user?.work || "",
      phone: user?.phone || "",
    });
  }, [user?.lives, user?.about, user?.languages, user?.work, user?.phone]);

  const hasChanges = useMemo(() => {
    return (
      form.lives !== (user?.lives || "") ||
      form.about !== (user?.about || "") ||
      form.languages !== (user?.languages || "") ||
      form.work !== (user?.work || "") ||
      form.phone !== (user?.phone || "")
    );
  }, [form, user]);

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
        lives: form.lives,
        about: form.about,
        languages: form.languages,
        work: form.work,
        phone: form.phone,
      });
      setSuccess("Profile updated.");
    } catch (err) {
      setError(err?.message || "Could not update your profile.");
    } finally {
      setIsSaving(false);
    }
  };

  const closeCropModal = () => {
    setIsCropModalOpen(false);
    setCropImageSrc(null);
  };

  const handlePhotoChange = (event) => {
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

    const reader = new FileReader();
    reader.onload = () => {
      setCropImageSrc(reader.result);
      setIsCropModalOpen(true);
    };
    reader.onerror = () => {
      setError("Could not read image file.");
    };
    reader.readAsDataURL(file);
  };

  const handleCropApply = async (croppedFile) => {
    setIsUploadingPhoto(true);
    setError("");
    setSuccess("");
    try {
      const fileUrl = await uploadProfilePhoto(croppedFile);
      await updateProfile({ profilePhotoUrl: fileUrl });
      setSuccess("Profile photo updated.");
      closeCropModal();
    } catch (err) {
      setError(err?.message || "Could not upload profile photo.");
    } finally {
      setIsUploadingPhoto(false);
    }
  };

  const displayName = firstName(user?.fullName);
  const joinedLabel =
    user?.joinedLabel ||
    (user?.createdAt
      ? `Joined ${new Intl.DateTimeFormat(undefined, {
          month: "long",
          year: "numeric",
        }).format(new Date(user.createdAt))}`
      : null);
  const tripsCount = user?.tripsCount ?? 0;
  const averageRating = user?.averageRating;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 md:px-6">
      <nav aria-label="Breadcrumb" className="mb-6 text-sm text-gray-500">
        <Link to="/" className="hover:text-gray-700">
          Home
        </Link>
        <span className="mx-2">›</span>
        <span className="text-gray-700">Profile</span>
      </nav>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-12 md:grid-cols-12 md:gap-20">
          <div className="md:col-span-5">
            <input
              ref={photoInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handlePhotoChange}
            />
            <button
              type="button"
              disabled={isUploadingPhoto || isCropModalOpen}
              onClick={() => photoInputRef.current?.click()}
              className="rounded-full bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Change profile photo
            </button>
            <p className="mt-3 text-xs text-gray-500">
              Add a face to the name. It&apos;ll help other hosts and guests recognize you at the
              beginning of a trip.
            </p>

            <h1 className="mb-4 mt-6 text-3xl font-bold text-gray-900">{displayName}</h1>

            <div className="mb-6">
              <label htmlFor="lives" className={fieldLabelClass}>
                Lives
              </label>
              <input
                id="lives"
                type="text"
                maxLength={100}
                value={form.lives}
                onChange={(event) =>
                  setForm((current) => ({ ...current, lives: event.target.value }))
                }
                placeholder="Toronto, ON"
                className={fieldInputClass}
              />
            </div>

            {joinedLabel && <p className="mt-2 text-sm text-gray-500">{joinedLabel}</p>}

            <div className="mt-8">
              <p className={fieldLabelClass}>Verified info</p>
              <div className="rounded-xl border border-gray-200 bg-white px-4">
                <VerifiedRow
                  label="Approved to drive"
                  verified={Boolean(user?.isApprovedToDrive)}
                  action={
                    <p className="mt-1 text-xs text-indigo-600">
                      Complete verification to unlock trips.
                    </p>
                  }
                />
                <VerifiedRow
                  label="Email address"
                  verified={Boolean(user?.hasEmail)}
                  action={null}
                />
                <VerifiedRow
                  label="Phone number"
                  verified={Boolean(user?.hasPhone)}
                  action={
                    <button
                      type="button"
                      onClick={() => phoneInputRef.current?.focus()}
                      className="mt-1 text-xs font-medium text-indigo-600 hover:text-indigo-700"
                    >
                      Add phone number
                    </button>
                  }
                />
              </div>
              <p className="mt-3 text-xs text-gray-400">
                Build trust with other users on our platform by verifying your contact information.
              </p>
            </div>

            <div className="mt-8">
              <label htmlFor="languages" className={fieldLabelClass}>
                Languages
              </label>
              <input
                id="languages"
                type="text"
                maxLength={150}
                value={form.languages}
                onChange={(event) =>
                  setForm((current) => ({ ...current, languages: event.target.value }))
                }
                placeholder="English, French"
                className={fieldInputClass}
              />
            </div>

            <div className="mt-6">
              <label htmlFor="work" className={fieldLabelClass}>
                Works
              </label>
              <input
                id="work"
                type="text"
                maxLength={100}
                value={form.work}
                onChange={(event) =>
                  setForm((current) => ({ ...current, work: event.target.value }))
                }
                placeholder="Software engineer"
                className={fieldInputClass}
              />
            </div>
          </div>

          <div className="md:col-span-7">
            <div className="flex flex-col items-center text-center sm:items-start sm:text-left">
              <div className="relative mb-6">
                <UserAvatar user={user} className="h-32 w-32 text-3xl" />
                {isUploadingPhoto && (
                  <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/40">
                    <Loader2 className="h-8 w-8 animate-spin text-white" aria-hidden="true" />
                    <span className="sr-only">Uploading photo</span>
                  </div>
                )}
              </div>

              <div className="mb-8 flex flex-wrap items-center gap-4 text-sm text-gray-600">
                <span>
                  <span className="font-semibold text-gray-900">{tripsCount}</span>{" "}
                  {tripsCount === 1 ? "trip" : "trips"}
                </span>
                {averageRating != null && (
                  <span className="inline-flex items-center gap-1">
                    <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                    <span className="font-semibold text-gray-900">
                      {Number(averageRating).toFixed(1)}
                    </span>
                    <span>rating</span>
                  </span>
                )}
              </div>
            </div>

            <div className="mb-6">
              <label htmlFor="about" className={fieldLabelClass}>
                About
              </label>
              <textarea
                id="about"
                rows={6}
                maxLength={2000}
                value={form.about}
                onChange={(event) =>
                  setForm((current) => ({ ...current, about: event.target.value }))
                }
                placeholder="Tell hosts and guests a little about yourself."
                className={`${fieldInputClass} resize-y`}
              />
            </div>

            <div className="mb-8">
              <label htmlFor="phone" className={fieldLabelClass}>
                Phone
              </label>
              <input
                ref={phoneInputRef}
                id="phone"
                type="tel"
                maxLength={32}
                value={form.phone}
                onChange={(event) =>
                  setForm((current) => ({ ...current, phone: event.target.value }))
                }
                placeholder="+1 514 555 0100"
                className={fieldInputClass}
              />
              <p className="mt-2 text-xs text-gray-500">
                Private. Used for trip coordination and verification.
              </p>
            </div>

            {error && (
              <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}
            {success && (
              <div className="mb-4 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700">
                {success}
              </div>
            )}

            <button
              type="submit"
              disabled={!hasChanges || isSaving}
              className="rounded-full bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isSaving ? "Saving..." : "Save profile"}
            </button>
          </div>
        </div>
      </form>

      <AvatarCropModal
        isOpen={isCropModalOpen}
        imageSrc={cropImageSrc}
        onCancel={closeCropModal}
        onApply={handleCropApply}
        isApplying={isUploadingPhoto}
      />
    </div>
  );
}
