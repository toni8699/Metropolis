import { avatarColorClass, avatarInitials, avatarLabel } from "@/shared/lib/avatar";

export default function UserAvatar({ user, name, className = "h-7 w-7 text-xs" }) {
  const label = user ? avatarLabel(user) : String(name || "").trim() || "Guest";
  const photoUrl = user?.profilePhotoUrl;

  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt=""
        className={`shrink-0 rounded-full object-cover ${className}`}
      />
    );
  }

  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-full font-semibold ${avatarColorClass(label)} ${className}`}
      aria-hidden="true"
    >
      {avatarInitials(label, user?.email)}
    </div>
  );
}
