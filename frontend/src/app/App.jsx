import { Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { AppPathRedirect } from "@/app/AppPathRedirect";
import { useAuth } from "@/context/AuthContext";
import BookingDetailsPage from "@/views/BookingDetailsPage";
import BookingCheckoutPage from "@/views/BookingCheckoutPage";
import ListingDetailPage from "@/views/ListingDetailPage";
import MapBrowsePage from "@/views/MapBrowsePage";
import HostDashboardPage from "@/views/HostDashboardPage";
import TripsPage from "@/views/TripsPage";
import InboxPage from "@/views/InboxPage";
import SavedListingsPage from "@/views/SavedListingsPage";
import AccountSettingsPage from "@/views/AccountSettingsPage";
import LoginPage from "@/views/LoginPage";
import VerifyEmailPage from "@/views/VerifyEmailPage";
import Layout from "@/layout/Layout";
import HostOnboardingFlow from "@/features/host/components/HostOnboardingFlow";
import SuccessListingPage from "@/features/host/SuccessListingPage";
import { RequireAuth, RequireRole } from "@/app/RouteGuards";
import { BrowseFiltersProvider } from "@/features/browse/hooks/useBrowseFilters.jsx";

function AppShell({ onSearch, onHome, hasSearched, searchParams }) {
  return (
    <BrowseFiltersProvider searchContext={{ hasSearched, searchParams }}>
      <Layout onSearch={onSearch} onHome={onHome}>
        <Outlet />
      </Layout>
    </BrowseFiltersProvider>
  );
}

function HostEntry() {
  const { isAdmin, isAuthenticated, isVerified, promptVerifyEmail } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAdmin || !isAuthenticated || isVerified) {
      return;
    }
    promptVerifyEmail();
    navigate("/app", { replace: true });
  }, [isAdmin, isAuthenticated, isVerified, navigate, promptVerifyEmail]);

  if (isAdmin) {
    return <Navigate to="/admin" replace />;
  }
  if (isAuthenticated && !isVerified) {
    return null;
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

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route
        path="/app"
        element={
          <AppShell
            onSearch={handleSearch}
            onHome={handleGoHome}
            hasSearched={hasSearched}
            searchParams={searchParams}
          />
        }
      >
        <Route
          index
          element={<MapBrowsePage hasSearched={hasSearched} searchParams={searchParams} />}
        />
        <Route path="listings/:listingId" element={<ListingDetailPage />} />
        <Route path="book/:id" element={<BookingCheckoutPage />} />
        <Route path="bookings/:bookingId" element={<BookingDetailsPage />} />
        <Route path="trips" element={<TripsPage />} />
        <Route path="saved" element={<SavedListingsPage />} />
        <Route path="messages" element={<InboxPage />} />
        <Route path="account" element={<AccountSettingsPage />} />
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Route>

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
      <Route path="/saved" element={<Navigate to="/app/saved" replace />} />
      <Route path="/messages" element={<Navigate to="/app/messages" replace />} />
      <Route path="/account" element={<Navigate to="/app/account" replace />} />
      <Route path="/book/:id" element={<AppPathRedirect prefix="/app/book" />} />
      <Route path="/listings/:listingId" element={<AppPathRedirect prefix="/app/listings" />} />
      <Route path="/bookings/:bookingId" element={<AppPathRedirect prefix="/app/bookings" />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}
