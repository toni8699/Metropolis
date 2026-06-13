import { Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";
import { AppPathRedirect } from "@/app/AppPathRedirect";
import { useAuth } from "@/context/AuthContext";
import BookingDetailsPage from "@/views/BookingDetailsPage";
import BookingCheckoutPage from "@/views/BookingCheckoutPage";
import ListingDetailPage from "@/views/ListingDetailPage";
import MapBrowsePage from "@/views/MapBrowsePage";
import OwnerDashboardPage from "@/views/OwnerDashboardPage";
import TripsPage from "@/views/TripsPage";
import InboxPage from "@/views/InboxPage";
import AdminDashboardPage from "@/views/AdminDashboardPage";
import AccountSettingsPage from "@/views/AccountSettingsPage";
import LoginPage from "@/views/LoginPage";
import Layout from "@/layout/Layout";
import HostOnboardingFlow from "@/features/host/components/HostOnboardingFlow";
import { RequireAuth, RequireRole } from "@/app/RouteGuards";

function HostEntry() {
  const { isAdmin } = useAuth();
  if (isAdmin) {
    return <Navigate to="/admin" replace />;
  }
  return <HostOnboardingFlow />;
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
    <Layout onSearch={handleSearch} onHome={handleGoHome}>
      <div className="w-full px-4 py-4 sm:px-5 md:px-6 lg:px-7 xl:px-8">
        <Routes>
          <Route
            path="/"
            element={
              <MapBrowsePage
                hasSearched={hasSearched}
                searchParams={searchParams}
              />
            }
          />
          <Route
            path="/app"
            element={
              <MapBrowsePage
                hasSearched={hasSearched}
                searchParams={searchParams}
              />
            }
          />
          <Route path="/listings/:listingId" element={<ListingDetailPage />} />
          <Route path="/app/listings/:listingId" element={<ListingDetailPage />} />
          <Route path="/book/:id" element={<BookingCheckoutPage />} />
          <Route path="/app/book/:id" element={<BookingCheckoutPage />} />
          <Route path="/bookings/:bookingId" element={<BookingDetailsPage />} />
          <Route path="/app/bookings/:bookingId" element={<BookingDetailsPage />} />
          <Route path="/trips" element={<TripsPage />} />
          <Route path="/app/trips" element={<TripsPage />} />
          <Route path="/messages" element={<InboxPage />} />
          <Route path="/app/messages" element={<InboxPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Layout>
  );

  const accountAppShell = (
    <Layout onSearch={handleSearch} onHome={handleGoHome}>
      <div className="w-full px-4 py-4 sm:px-5 md:px-6 lg:px-7 xl:px-8">
        <AccountSettingsPage />
      </div>
    </Layout>
  );

  return (
    <Routes>
      <Route path="/" element={mainAppShell} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/app/account" element={accountAppShell} />
      <Route path="/app/*" element={mainAppShell} />

      <Route element={<RequireAuth />}>
        <Route path="/host" element={<HostEntry />} />
        <Route path="/host/dashboard" element={<OwnerDashboardPage />} />
        <Route element={<RequireRole roles={["admin"]} />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
        </Route>
      </Route>

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
