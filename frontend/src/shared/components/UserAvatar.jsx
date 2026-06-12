import { avatarColorClass, avatarInitials, avatarLabel } from "@/shared/lib/avatar";

export default function UserAvatar({ user, className = "h-7 w-7 text-xs" }) {
  const label = avatarLabel(user);
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
