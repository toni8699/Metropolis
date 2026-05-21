import { Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "./context/AuthContext";
import BookingDetailsPage from "./pages/BookingDetailsPage";
import BookingCheckoutPage from "./pages/BookingCheckoutPage";
import ListingDetailPage from "./pages/ListingDetailPage";
import MapBrowsePage from "./pages/MapBrowsePage";
import OwnerDashboardPage from "./pages/OwnerDashboardPage";
import TripsPage from "./pages/TripsPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
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
      <div className="w-full px-4 py-5 sm:px-6 md:px-10 lg:px-12 xl:px-20">
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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Layout>
  );

  return (
    <Routes>
      <Route path="/" element={mainAppShell} />
      <Route path="/app/*" element={mainAppShell} />

      <Route element={<RequireAuth />}>
        <Route path="/host" element={<HostEntry />} />
        <Route path="/host/dashboard" element={<OwnerDashboardPage />} />
        <Route element={<RequireRole roles={["admin"]} />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}
