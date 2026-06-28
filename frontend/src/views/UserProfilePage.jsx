import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BadgeCheck, Star } from "lucide-react";
import UserAvatar from "@/shared/components/UserAvatar";
import PageShell from "@/shared/components/PageShell";
import { apiGet } from "@/shared/api/api";

const detailLabelClass =
  "mb-1 block text-xs font-extrabold uppercase tracking-wider text-vroom-muted";

function DetailField({ label, value }) {
  if (!value) return null;
  return (
    <div className="mb-6">
      <p className={detailLabelClass}>{label}</p>
      <p className="whitespace-pre-line text-sm text-vroom-text">{value}</p>
    </div>
  );
}

export default function UserProfilePage() {
  const { userId } = useParams();
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError("");
    apiGet(`/api/users/${userId}`)
      .then((data) => {
        if (!cancelled) setUser(data?.user || null);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message || "Could not load this profile.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (isLoading) {
    return (
      <PageShell maxWidth="4xl" card className="px-5 py-8 md:px-7">
        <div className="flex flex-col items-center gap-4">
          <div className="h-36 w-36 animate-pulse rounded-full bg-gray-200" />
          <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
          <div className="h-4 w-32 animate-pulse rounded bg-gray-100" />
        </div>
      </PageShell>
    );
  }

  if (error || !user) {
    return (
      <PageShell maxWidth="4xl" card className="px-5 py-12 text-center md:px-7">
        <h1 className="text-2xl font-extrabold text-vroom-text">Profile unavailable</h1>
        <p className="mt-2 text-sm text-gray-500">{error || "This user could not be found."}</p>
        <Link
          to="/app"
          className="mt-6 inline-block rounded-full border-2 border-black border-b-4 bg-vroom-accent px-6 py-2.5 text-sm font-extrabold text-white transition active:border-b-0"
        >
          Back to browsing
        </Link>
      </PageShell>
    );
  }

  const displayName = user.fullName || "VROOM user";
  const tripsCount = user.tripsCount ?? 0;
  const averageRating = user.averageRating;

  return (
    <PageShell maxWidth="4xl" card className="px-5 py-8 md:px-7">
      <div className="grid grid-cols-1 gap-12 md:grid-cols-12 md:gap-16">
        <div className="flex flex-col items-center text-center md:col-span-5 md:items-start md:text-left">
          <UserAvatar
            user={user}
            className="mb-6 h-36 w-36 border-4 border-vroom-accent text-3xl"
          />
          <h1 className="text-4xl font-extrabold text-vroom-text">{displayName}</h1>
          {user.joinedLabel && (
            <p className="mt-2 text-sm text-gray-500">{user.joinedLabel}</p>
          )}

          <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-sm text-gray-600 md:justify-start">
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

          <div className="mt-6 flex flex-wrap items-center justify-center gap-2 md:justify-start">
            {user.isHost && (
              <span className="rounded-full border-2 border-black bg-vroom-surface px-4 py-1.5 text-xs font-extrabold text-vroom-text">
                Host
              </span>
            )}
            {user.isVerified && (
              <span className="inline-flex items-center gap-1 rounded-full border-2 border-black bg-vroom-surface px-4 py-1.5 text-xs font-extrabold text-vroom-text">
                <BadgeCheck className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                Verified
              </span>
            )}
          </div>
        </div>

        <div className="md:col-span-7">
          {user.about ? (
            <DetailField label="About" value={user.about} />
          ) : (
            <p className="mb-6 text-sm italic text-gray-400">
              {displayName} hasn&apos;t added a bio yet.
            </p>
          )}
          <DetailField label="Lives" value={user.lives} />
          <DetailField label="Languages" value={user.languages} />
          <DetailField label="Works" value={user.work} />
        </div>
      </div>
    </PageShell>
  );
}
