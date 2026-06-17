import { RefreshCw } from "lucide-react";

export default function HostDashboardHeader({ title, isAdmin, isSyncingFleet, onSyncFleet }) {
  return (
    <header className="sticky top-0 z-10 flex h-20 shrink-0 items-center justify-between border-b-4 border-black bg-vroom-card px-11">
      <h1 className="text-3xl font-extrabold text-vroom-heading">{title}</h1>
      {isAdmin && (
        <button
          type="button"
          onClick={onSyncFleet}
          disabled={isSyncingFleet}
          className="flex items-center gap-2 rounded-full border-2 border-black border-b-4 bg-vroom-accent px-4 py-2 font-extrabold text-white transition active:border-b-0 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isSyncingFleet ? "animate-spin" : ""}`} />
          {isSyncingFleet ? "Syncing..." : "Sync Fleet Now"}
        </button>
      )}
    </header>
  );
}
