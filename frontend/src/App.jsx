import { Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";
import { AppPathRedirect } from "./components/AppPathRedirect";
import { useAuth } from "./context/AuthContext";
import BookingDetailsPage from "./pages/BookingDetailsPage";
import BookingCheckoutPage from "./pages/BookingCheckoutPage";
import ListingDetailPage from "./pages/ListingDetailPage";
import MapBrowsePage from "./pages/MapBrowsePage";
import OwnerDashboardPage from "./pages/OwnerDashboardPage";
import TripsPage from "./pages/TripsPage";
import InboxPage from "./pages/InboxPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import AccountSettingsPage from "./pages/AccountSettingsPage";
import Layout from "./components/Layout";
import HostOnboardingFlow from "./components/HostOnboardingFlow";
import { RequireAuth, RequireRole } from "./components/RouteGuards";

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
      <div className="w-full px-3 py-3 sm:px-4 md:px-5 lg:px-6 xl:px-7">
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
          <Route path="/app/account" element={<AccountSettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Layout>
  );

  const accountAppShell = (
    <Layout onSearch={handleSearch} onHome={handleGoHome}>
      <div className="w-full px-3 py-3 sm:px-4 md:px-5 lg:px-6 xl:px-7">
        <AccountSettingsPage />
      </div>
    </Layout>
  );

  return (
    <Routes>
      <Route path="/" element={mainAppShell} />
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
