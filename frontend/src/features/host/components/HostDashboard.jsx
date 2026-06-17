import { useMemo, useState } from "react";
import {
  Building2,
  CalendarDays,
  CarFront,
  LayoutDashboard,
  RefreshCw,
  ShieldCheck,
  UploadCloud,
  Users,
} from "lucide-react";
import { useLocation } from "react-router-dom";
import Layout from "@/layout/Layout";
import { useAuth } from "@/context/AuthContext";
import { useGoogleMaps } from "@/context/GoogleMapsProvider";
import { useHostDashboardData } from "@/features/host/hooks/useHostDashboardData";
import { useListingForm } from "@/features/host/hooks/useListingForm";
import ListingsTableSection from "@/features/host/components/ListingsTableSection";
import MapPickerModal from "@/features/host/components/MapPickerModal";
import OverviewPanel from "@/features/host/components/panels/OverviewPanel";
import ListingFormPanel from "@/features/host/components/panels/ListingFormPanel";
import BookingsPanel from "@/features/host/components/panels/BookingsPanel";
import UsersPanel from "@/features/host/components/panels/UsersPanel";
import KycPanel from "@/features/host/components/panels/KycPanel";

function getNavItems(isAdmin) {
  const items = [{ id: "overview", label: "Overview", icon: LayoutDashboard }];
  if (isAdmin) {
    items.push(
      { id: "fleet_listings", label: "Fleet Listings", icon: CarFront },
      { id: "host_listings", label: "Host Listings", icon: Building2 },
      { id: "create_listing", label: "Create Listing", icon: UploadCloud },
      { id: "users", label: "Users", icon: Users },
      { id: "kyc", label: "KYC Queue", icon: ShieldCheck },
    );
  } else {
    items.push(
      { id: "listings", label: "Listings", icon: CarFront },
      { id: "create_listing", label: "Create Listing", icon: UploadCloud },
    );
  }
  items.push({ id: "bookings", label: "Bookings", icon: CalendarDays });
  return items;
}

const pageTitles = {
  overview: "Overview",
  listings: "Manage Listings",
  fleet_listings: "Fleet Listings",
  host_listings: "Host Listings",
  create_listing: "Create Listing",
  users: "Users",
  kyc: "KYC Queue",
  bookings: "Bookings",
};

export default function HostDashboard({ mode = "admin" }) {
  const location = useLocation();
  const { refreshMe } = useAuth();
  const isAdmin = mode === "admin";
  const navItems = useMemo(() => getNavItems(isAdmin), [isAdmin]);
  const [activeTab, setActiveTab] = useState("overview");
  const { apiKey, isLoaded: isMapLoaded } = useGoogleMaps();

  const data = useHostDashboardData({ isAdmin, pathname: location.pathname });
  const form = useListingForm({
    isAdmin,
    companyLocations: data.companyLocations,
    isMapLoaded,
    refresh: data.refresh,
    refreshMe,
    setError: data.setError,
    setSuccess: data.setSuccess,
    setActiveTab,
  });

  const {
    analytics,
    bookings,
    listings,
    hostListings,
    users,
    kycQueue,
    companyLocations,
    isLoading,
    isSyncingFleet,
    bookingActionId,
    error,
    success,
    syncFleet,
    deleteListing,
    handleBookingDecision,
    decideKyc,
  } = data;

  const activePageTitle = useMemo(
    () => pageTitles[activeTab] || (isAdmin ? "Admin Dashboard" : "Host Dashboard"),
    [activeTab, isAdmin],
  );

  const isListingsTab =
    activeTab === "listings" || activeTab === "fleet_listings" || activeTab === "host_listings";

  const listingsTabId = isAdmin ? "fleet_listings" : "listings";

  const requestTabChange = (tabId) => {
    if (activeTab === "create_listing" && tabId !== "create_listing" && !form.confirmLeaveIfDirty()) {
      return;
    }
    setActiveTab(tabId);
  };

  return (
    <Layout>
      <div className="fixed inset-x-0 top-28 md:top-[104px] bottom-0 z-0 flex border-t-4 border-black bg-[#D0F0C0] overflow-hidden">
        <aside className="w-64 shrink-0 border-r-4 border-black bg-[#f5f5d0] flex flex-col overflow-y-auto">
          <div className="p-6 border-b-2 border-black">
            <p className="text-2xl font-extrabold text-[#183B1E]">
              {isAdmin ? "VROOM Admin" : "VROOM Host"}
            </p>
          </div>
          <nav className="flex-1 py-6 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => requestTabChange(item.id)}
                  className={`w-[calc(100%-2rem)] mx-4 px-4 py-2 rounded-lg flex items-center gap-3 text-sm transition ${
                    isActive
                      ? "border-2 border-black bg-[#dbe8be] text-[#183B1E] font-extrabold shadow-[3px_3px_0px_0px_rgba(24,59,30,0.35)]"
                      : "text-[#35593b] hover:bg-[#f5f5d0]"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </aside>

        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <header className="sticky top-0 z-10 flex h-20 shrink-0 items-center justify-between border-b-4 border-black bg-[#f5f5d0] px-11">
            <h1 className="text-3xl font-extrabold text-[#183B1E]">{activePageTitle}</h1>
            {isAdmin && (
              <button
                onClick={syncFleet}
                disabled={isSyncingFleet}
                className="rounded-full border-2 border-black border-b-4 bg-[#E34B31] px-4 py-2 font-extrabold text-white flex items-center gap-2 transition active:border-b-0 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isSyncingFleet ? "animate-spin" : ""}`} />
                {isSyncingFleet ? "Syncing..." : "Sync Fleet Now"}
              </button>
            )}
          </header>

          <main className="pb-10">
            {error && (
              <div className="mx-11 mt-6 rounded-xl border-2 border-black bg-[#ffd8cf] p-3 text-sm font-semibold text-[#7a2215]">
                {error}
              </div>
            )}
            {success && (
              <div className="mx-11 mt-6 rounded-xl border-2 border-black bg-[#dbe8be] p-3 text-sm font-semibold text-[#183B1E]">
                {success}
              </div>
            )}

            {activeTab === "overview" && (
              <OverviewPanel
                analytics={analytics}
                bookings={bookings}
                listings={listings}
                isAdmin={isAdmin}
              />
            )}

            {activeTab === "create_listing" && (
              <ListingFormPanel
                form={form}
                isAdmin={isAdmin}
                companyLocations={companyLocations}
                apiKey={apiKey}
                isMapLoaded={isMapLoaded}
                listingsTabId={listingsTabId}
              />
            )}

            {isListingsTab && (
              <ListingsTableSection
                title={
                  activeTab === "host_listings"
                    ? "Host Listings"
                    : isAdmin
                      ? "Fleet Listings"
                      : "My Listings"
                }
                listings={activeTab === "host_listings" ? hostListings : listings}
                showHostColumn={activeTab === "host_listings"}
                showTypeColumn={isAdmin && activeTab !== "host_listings"}
                showAddButton={activeTab !== "host_listings"}
                onAdd={() => requestTabChange("create_listing")}
                onEdit={form.startEditListing}
                onDelete={deleteListing}
              />
            )}

            {isAdmin && activeTab === "kyc" && (
              <KycPanel kycQueue={kycQueue} onDecision={decideKyc} />
            )}

            {isAdmin && activeTab === "users" && <UsersPanel users={users} />}

            {activeTab === "bookings" && (
              <BookingsPanel
                isAdmin={isAdmin}
                bookings={bookings}
                bookingActionId={bookingActionId}
                onDecision={handleBookingDecision}
              />
            )}

            {form.isMapModalOpen && (
              <MapPickerModal
                apiKey={apiKey}
                isMapLoaded={isMapLoaded}
                tempLocation={form.tempLocation}
                isReverseGeocoding={form.isReverseGeocoding}
                onPinMove={form.handlePinDrop}
                onConfirm={form.confirmMapPickerLocation}
                onClose={() => form.setIsMapModalOpen(false)}
              />
            )}

            {isLoading && (
              <div className="mx-11 rounded-md bg-gray-100 p-3 text-sm text-gray-600">
                Loading dashboard data...
              </div>
            )}
          </main>
        </div>
      </div>
    </Layout>
  );
}
