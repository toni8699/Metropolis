import { Link } from "react-router-dom";
import { Car } from "lucide-react";

export default function HostDashboardSidebar({ isAdmin, navItems, activeTab, onTabChange }) {
  return (
    <aside className="flex w-64 shrink-0 flex-col overflow-y-auto border-r-4 border-black bg-vroom-card">
      <div className="border-b-2 border-black p-6">
        <p className="text-2xl font-extrabold text-vroom-heading">
          {isAdmin ? "VROOM Admin" : "VROOM Host"}
        </p>
      </div>
      <nav className="flex-1 space-y-2 py-6">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onTabChange(item.id)}
              className={`mx-4 flex w-[calc(100%-2rem)] items-center gap-3 rounded-lg px-4 py-2 text-sm transition ${
                isActive
                  ? "border-2 border-black bg-vroom-sage font-extrabold text-vroom-heading shadow-neoSm"
                  : "text-vroom-muted hover:bg-vroom-card"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </nav>
      {!isAdmin && (
        <div className="border-t-2 border-black p-4">
          <Link
            to="/app"
            className="flex items-center gap-3 rounded-lg border-2 border-black bg-vroom-surface px-4 py-2 text-sm font-semibold text-vroom-heading transition hover:bg-vroom-sage"
          >
            <Car className="h-4 w-4" />
            Switch to renting
          </Link>
        </div>
      )}
    </aside>
  );
}
