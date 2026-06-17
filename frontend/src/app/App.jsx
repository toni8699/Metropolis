import { Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";
import { AppPathRedirect } from "@/app/AppPathRedirect";
import { useAuth } from "@/context/AuthContext";
import BookingDetailsPage from "@/views/BookingDetailsPage";
import BookingCheckoutPage from "@/views/BookingCheckoutPage";
import ListingDetailPage from "@/views/ListingDetailPage";
import MapBrowsePage from "@/views/MapBrowsePage";
import HostDashboardPage from "@/views/HostDashboardPage";
import TripsPage from "@/views/TripsPage";
import InboxPage from "@/views/InboxPage";
import AccountSettingsPage from "@/views/AccountSettingsPage";
import LoginPage from "@/views/LoginPage";
import Layout from "@/layout/Layout";
import HostOnboardingFlow from "@/features/host/components/HostOnboardingFlow";
import SuccessListingPage from "@/features/host/SuccessListingPage";
import { RequireAuth, RequireRole } from "@/app/RouteGuards";

function AppShell({ children, onSearch, onHome }) {
  return <Layout onSearch={onSearch} onHome={onHome}>{children}</Layout>;
}

function HostEntry() {
  const { isAdmin } = useAuth();
  if (isAdmin) {
    return <Navigate to="/admin" replace />;
  }
  return <HostOnboardingFlow />;
}

function appRoutes(hasSearched, searchParams) {
  return (
    <>
      <Route
        index
        element={<MapBrowsePage hasSearched={hasSearched} searchParams={searchParams} />}
      />
      <Route path="listings/:listingId" element={<ListingDetailPage />} />
      <Route path="book/:id" element={<BookingCheckoutPage />} />
      <Route path="bookings/:bookingId" element={<BookingDetailsPage />} />
      <Route path="trips" element={<TripsPage />} />
      <Route path="messages" element={<InboxPage />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </>
  );
}

export default function App() {
  const [hasSearched, setHasSearched] = useState(false);
  const [searchParams, setSearchParams] = useState({
    location: "",
    pickupDate: "",
    returnDate: "",
  });

  const handleSearch = (params) => {
    setSearchParams(params);
    setHasSearched(true);
  };

  const handleGoHome = () => {
    setHasSearched(false);
  };

  const mainAppShell = (
    <AppShell onSearch={handleSearch} onHome={handleGoHome}>
      <Routes>{appRoutes(hasSearched, searchParams)}</Routes>
    </AppShell>
  );

  const accountAppShell = (
    <AppShell onSearch={handleSearch} onHome={handleGoHome}>
      <AccountSettingsPage />
    </AppShell>
  );

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/app/account" element={accountAppShell} />
      <Route path="/app/*" element={mainAppShell} />

      <Route element={<RequireAuth />}>
        <Route path="/host" element={<HostEntry />} />
        <Route path="/host/success/:listingId" element={<SuccessListingPage />} />
        <Route path="/host/dashboard" element={<HostDashboardPage mode="owner" />} />
        <Route element={<RequireRole roles={["admin"]} />}>
          <Route path="/admin" element={<HostDashboardPage mode="admin" />} />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="/trips" element={<Navigate to="/app/trips" replace />} />
      <Route path="/messages" element={<Navigate to="/app/messages" replace />} />
      <Route path="/account" element={<Navigate to="/app/account" replace />} />
      <Route path="/book/:id" element={<AppPathRedirect prefix="/app/book" />} />
      <Route path="/listings/:listingId" element={<AppPathRedirect prefix="/app/listings" />} />
      <Route path="/bookings/:bookingId" element={<AppPathRedirect prefix="/app/bookings" />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}
