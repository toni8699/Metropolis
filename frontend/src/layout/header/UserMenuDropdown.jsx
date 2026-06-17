export default function UserMenuDropdown({
  isAuthenticated,
  user,
  onLogin,
  onSignup,
  onOpenAccount,
  onOpenTrips,
  onOpenMessages,
  onOpenHostDashboard,
  onOpenAdminDashboard,
  onLogout,
  isAdmin,
  showHostDashboard,
}) {
  const itemClass =
    "w-full rounded-xl border-2 border-transparent px-3 py-2 text-left text-sm font-medium text-vroom-heading hover:border-black hover:bg-vroom-sage";

  return (
    <div className="absolute right-0 top-full z-[70] mt-2 w-56 rounded-2xl border-2 border-black bg-vroom-surface p-2 shadow-neo">
      {!isAuthenticated ? (
        <>
          <button type="button" onClick={onLogin} className={itemClass}>
            Log in
          </button>
          <button type="button" onClick={onSignup} className={itemClass}>
            Sign up
          </button>
        </>
      ) : (
        <>
          <div className="border-b-2 border-black px-3 py-2">
            <p className="truncate text-sm font-semibold text-vroom-heading">
              {user?.fullName || user?.email || "Your account"}
            </p>
            {user?.fullName && (
              <p className="mt-0.5 truncate text-xs text-vroom-muted">{user.email}</p>
            )}
          </div>
          <button type="button" onClick={onOpenAccount} className={`mt-1 ${itemClass}`}>
            Account settings
          </button>
          <button type="button" onClick={onOpenMessages} className={itemClass}>
            Messages
          </button>
          <button type="button" onClick={onOpenTrips} className={itemClass}>
            Trips
          </button>
          {showHostDashboard && (
            <button type="button" onClick={onOpenHostDashboard} className={itemClass}>
              Host Dashboard
            </button>
          )}
          {isAdmin && (
            <button type="button" onClick={onOpenAdminDashboard} className={itemClass}>
              Admin Dashboard
            </button>
          )}
          <button type="button" onClick={onLogout} className={itemClass}>
            Log out
          </button>
        </>
      )}
    </div>
  );
}
