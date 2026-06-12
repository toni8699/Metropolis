export function avatarLabel(user) {
  const fullName = String(user?.fullName || "").trim();
  if (fullName) return fullName;
  const email = String(user?.email || "").trim();
  if (email) return email;
  return "Guest";
}

export function avatarInitials(name, fallbackEmail) {
  const parts = String(name || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0].charAt(0)}${parts[1].charAt(0)}`.toUpperCase().slice(0, 2);
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  const email = String(fallbackEmail || "").trim();
  if (email) return email.slice(0, 2).toUpperCase();
  return "G";
}

export function avatarColorClass(name) {
  const palette = [
    "bg-indigo-100 text-indigo-700",
    "bg-emerald-100 text-emerald-700",
    "bg-amber-100 text-amber-800",
    "bg-rose-100 text-rose-700",
    "bg-sky-100 text-sky-700",
  ];
  const seed = String(name || "guest")
    .split("")
    .reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return palette[seed % palette.length];
}
