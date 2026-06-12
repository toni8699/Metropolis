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
  canAdmin,
  showHostDashboard,
}) {
  return (
    <div className="absolute right-0 top-full z-[70] mt-2 w-56 rounded-2xl border border-gray-200 bg-white p-2 shadow-xl">
      {!isAuthenticated ? (
        <>
          <button
            onClick={onLogin}
            className="w-full rounded-xl px-3 py-2 text-left text-sm font-medium hover:bg-gray-50"
          >
            Log in
          </button>
          <button
            onClick={onSignup}
            className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-gray-50"
          >
            Sign up
          </button>
        </>
      ) : (
        <>
          <div className="border-b border-gray-100 px-3 py-2">
            <p className="truncate text-sm font-semibold text-gray-900">
              {user?.fullName || user?.email || "Your account"}
            </p>
            {user?.fullName && (
              <p className="mt-0.5 truncate text-xs text-gray-500">{user.email}</p>
            )}
          </div>
          <button
            onClick={onOpenAccount}
            className="mt-1 w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-gray-50"
          >
            Account settings
          </button>
          <button
            onClick={onOpenMessages}
            className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-gray-50"
          >
            Messages
          </button>
          <button
            onClick={onOpenTrips}
            className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-gray-50"
          >
            Trips
          </button>
          {showHostDashboard && (
            <button
              onClick={onOpenHostDashboard}
              className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-gray-50"
            >
              Host Dashboard
            </button>
          )}
          {canAdmin && (
            <button
              onClick={onOpenAdminDashboard}
              className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-gray-50"
            >
              Admin Dashboard
            </button>
          )}
          <button
            onClick={onLogout}
            className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-gray-50"
          >
            Log out
          </button>
        </>
      )}
    </div>
  );
}
