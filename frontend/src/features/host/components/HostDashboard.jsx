import { useMemo } from "react";
import { useLocation } from "react-router-dom";
import Layout from "@/layout/Layout";
import { useAuth } from "@/context/AuthContext";
import { useGoogleMaps } from "@/context/GoogleMapsProvider";
import { useHostDashboardData } from "@/features/host/hooks/useHostDashboardData";
import { useListingForm } from "@/features/host/hooks/useListingForm";
import { useHostDashboardTabs } from "@/features/host/hooks/useHostDashboardTabs";
import { getNavItems, getPageTitle } from "@/features/host/lib/dashboardNav";
import HostDashboardShell from "@/features/host/components/dashboard/HostDashboardShell";
import HostDashboardSidebar from "@/features/host/components/dashboard/HostDashboardSidebar";
import HostDashboardHeader from "@/features/host/components/dashboard/HostDashboardHeader";
import HostDashboardAlerts from "@/features/host/components/dashboard/HostDashboardAlerts";
import HostDashboardContent from "@/features/host/components/dashboard/HostDashboardContent";

export default function HostDashboard({ mode = "admin" }) {
  const location = useLocation();
  const { refreshMe } = useAuth();
  const isAdmin = mode === "admin";
  const navItems = useMemo(() => getNavItems(isAdmin), [isAdmin]);
  const { apiKey, isLoaded: isMapLoaded } = useGoogleMaps();

  const data = useHostDashboardData({ isAdmin, pathname: location.pathname });
  const { activeTab, setActiveTab, requestTabChange, setConfirmLeaveIfDirty } =
    useHostDashboardTabs();

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

  setConfirmLeaveIfDirty(form.confirmLeaveIfDirty);

  const activePageTitle = useMemo(
    () => getPageTitle(activeTab, isAdmin),
    [activeTab, isAdmin],
  );

  return (
    <Layout>
      <HostDashboardShell>
        <HostDashboardSidebar
          isAdmin={isAdmin}
          navItems={navItems}
          activeTab={activeTab}
          onTabChange={requestTabChange}
        />
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <HostDashboardHeader
            title={activePageTitle}
            isAdmin={isAdmin}
            isSyncingFleet={data.isSyncingFleet}
            onSyncFleet={data.syncFleet}
          />
          <HostDashboardAlerts error={data.error} success={data.success} />
          <HostDashboardContent
            activeTab={activeTab}
            isAdmin={isAdmin}
            isLoading={data.isLoading}
            analytics={data.analytics}
            bookings={data.bookings}
            listings={data.listings}
            hostListings={data.hostListings}
            users={data.users}
            kycQueue={data.kycQueue}
            companyLocations={data.companyLocations}
            bookingActionId={data.bookingActionId}
            apiKey={apiKey}
            isMapLoaded={isMapLoaded}
            form={form}
            onRequestTabChange={requestTabChange}
            onDeleteListing={data.deleteListing}
            onBookingDecision={data.handleBookingDecision}
            onKycDecision={data.decideKyc}
          />
        </div>
      </HostDashboardShell>
    </Layout>
  );
}
