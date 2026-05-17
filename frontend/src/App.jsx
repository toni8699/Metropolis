import { Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";
import BookingDetailsPage from "./pages/BookingDetailsPage";
import ListingDetailPage from "./pages/ListingDetailPage";
import MapBrowsePage from "./pages/MapBrowsePage";
import OwnerDashboardPage from "./pages/OwnerDashboardPage";
import Layout from "./components/Layout";
import { apiPost, setAccessToken } from "./lib/api";

async function quickDemoLogin(role = "RENTER") {
  const email = role === "OWNER" ? "owner_demo@example.com" : "renter_demo@example.com";
  const password = "testpass123";
  await apiPost("/api/auth/register", { email, password, role });
  const login = await apiPost("/api/auth/login", { email, password });
  if (login.token) {
    setAccessToken(login.token);
    window.location.reload();
  }
}

export default function App() {
  const [hasSearched, setHasSearched] = useState(false);

  return (
    <Layout onSearch={() => setHasSearched(true)}>
      <div className="flex w-full items-center justify-end gap-2 px-4 py-3 sm:px-6 md:px-10 lg:px-12 xl:px-20">
        <button
          className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          onClick={() => quickDemoLogin("RENTER")}
        >
          Demo renter login
        </button>
        <button
          className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          onClick={() => quickDemoLogin("OWNER")}
        >
          Demo owner login
        </button>
      </div>
      <div className="w-full px-4 py-5 sm:px-6 md:px-10 lg:px-12 xl:px-20">
        <Routes>
          <Route path="/" element={<MapBrowsePage hasSearched={hasSearched} />} />
          <Route path="/listings/:listingId" element={<ListingDetailPage />} />
          <Route path="/bookings/:bookingId" element={<BookingDetailsPage />} />
          <Route path="/owner" element={<OwnerDashboardPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Layout>
  );
}
