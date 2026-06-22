import { Mail, Menu } from "lucide-react";
import { Link } from "react-router-dom";
import UserAvatar from "@/shared/components/UserAvatar";
import UserMenuDropdown from "@/layout/header/UserMenuDropdown";

export default function HeaderUserMenu({
  menuRef,
  variant = "mobile",
  isAuthenticated,
  user,
  isUserMenuOpen,
  onToggleMenu,
  onLogin,
  onSignup,
  onOpenAccount,
  onOpenTrips,
  onOpenSaved,
  onOpenMessages,
  onOpenHostDashboard,
  onOpenAdminDashboard,
  onLogout,
  showHostDashboard,
  isAdmin,
}) {
  const isMobile = variant === "mobile";
  const buttonPadding = isMobile ? "p-1 pl-2.5" : "p-1.5 pl-2.5";
  const wrapperClass = isMobile ? "relative flex items-center gap-1 md:hidden" : "relative";

  return (
    <div ref={menuRef} className={wrapperClass}>
      {isMobile && isAuthenticated && (
        <Link
          to="/app/messages"
          className="rounded-full border-2 border-black bg-vroom-coral p-2 text-vroom-text transition hover:scale-105"
          aria-label="Messages"
        >
          <Mail className="h-6 w-6" />
        </Link>
      )}
      <button
        type="button"
        onClick={onToggleMenu}
        className={`flex items-center gap-1.5 rounded-full border-2 border-black bg-vroom-surface ${buttonPadding} transition hover:shadow-neoSm`}
        aria-label="User menu"
      >
        <Menu className="h-6 w-6 text-vroom-text" />
        {isAuthenticated ? (
          <UserAvatar user={user} className="h-9 w-9 text-sm ring-2 ring-vroom-accent" />
        ) : (
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-vroom-gold text-sm font-extrabold text-vroom-text">
            G
          </div>
        )}
      </button>
      {isUserMenuOpen && (
        <UserMenuDropdown
          isAuthenticated={isAuthenticated}
          user={user}
          onLogin={onLogin}
          onSignup={onSignup}
          onOpenAccount={onOpenAccount}
          onOpenTrips={onOpenTrips}
          onOpenSaved={onOpenSaved}
          onOpenMessages={onOpenMessages}
          onOpenHostDashboard={onOpenHostDashboard}
          onOpenAdminDashboard={onOpenAdminDashboard}
          onLogout={onLogout}
          showHostDashboard={showHostDashboard}
          isAdmin={isAdmin}
        />
      )}
    </div>
  );
}
