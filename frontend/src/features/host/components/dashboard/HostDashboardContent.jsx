import ListingsTableSection from "@/features/host/components/ListingsTableSection";
import MapPickerModal from "@/features/host/components/MapPickerModal";
import OverviewPanel from "@/features/host/components/panels/OverviewPanel";
import ListingFormPanel from "@/features/host/components/panels/ListingFormPanel";
import BookingsPanel from "@/features/host/components/panels/BookingsPanel";
import UsersPanel from "@/features/host/components/panels/UsersPanel";
import KycPanel from "@/features/host/components/panels/KycPanel";
import PayoutsPanel from "@/features/host/components/panels/PayoutsPanel";
import AvailabilityPanel from "@/features/host/components/panels/AvailabilityPanel";
import {
  TAB,
  isListingsTab,
  listingsTabId,
  listingsTableTitle,
} from "@/features/host/lib/dashboardNav";

export default function HostDashboardContent({
  activeTab,
  isAdmin,
  isLoading,
  analytics,
  bookings,
  listings,
  hostListings,
  users,
  kycQueue,
  companyLocations,
  bookingActionId,
  apiKey,
  isMapLoaded,
  form,
  onRequestTabChange,
  onDeleteListing,
  onToggleListingStatus,
  onBookingDecision,
  onCancelBooking,
  onKycDecision,
  connectStatus,
  recentPayouts,
  onRefreshPayouts,
}) {
  return (
    <main className="pb-10">
      {isLoading && (
        <div className="mx-11 mt-6 rounded-md bg-gray-100 p-3 text-sm text-gray-600">
          Loading dashboard data...
        </div>
      )}

      {activeTab === TAB.overview && (
        <OverviewPanel
          analytics={analytics}
          bookings={bookings}
          listings={listings}
          isAdmin={isAdmin}
        />
      )}

      {activeTab === TAB.create_listing && (
        <ListingFormPanel
          form={form}
          isAdmin={isAdmin}
          companyLocations={companyLocations}
          apiKey={apiKey}
          isMapLoaded={isMapLoaded}
          listingsTabId={listingsTabId(isAdmin)}
        />
      )}

      {isListingsTab(activeTab) && (
        <ListingsTableSection
          title={listingsTableTitle(activeTab, isAdmin)}
          listings={activeTab === TAB.host_listings ? hostListings : listings}
          showHostColumn={activeTab === TAB.host_listings}
          showTypeColumn={isAdmin && activeTab !== TAB.host_listings}
          showAddButton={activeTab !== TAB.host_listings}
          onAdd={() => onRequestTabChange(TAB.create_listing)}
          onEdit={form.startEditListing}
          onDelete={onDeleteListing}
          onToggleStatus={onToggleListingStatus}
        />
      )}

      {isAdmin && activeTab === TAB.kyc && (
        <KycPanel kycQueue={kycQueue} onDecision={onKycDecision} />
      )}

      {isAdmin && activeTab === TAB.users && <UsersPanel users={users} />}

      {activeTab === TAB.bookings && (
        <BookingsPanel
          isAdmin={isAdmin}
          bookings={bookings}
          bookingActionId={bookingActionId}
          onDecision={onBookingDecision}
          onCancelBooking={onCancelBooking}
        />
      )}

      {!isAdmin && activeTab === TAB.payouts && (
        <PayoutsPanel
          connectStatus={connectStatus}
          recentPayouts={recentPayouts}
          onRefresh={onRefreshPayouts}
        />
      )}

      {!isAdmin && activeTab === TAB.availability && (
        <AvailabilityPanel listings={listings} />
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
    </main>
  );
}
