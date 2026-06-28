import { useCallback, useEffect, useState } from "react";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/shared/api/api";

const EMPTY_LOCATIONS = {
  areas: [],
  branches: [],
  parkingSpots: [],
  vehicleClasses: [],
};

/** Owns all dashboard entity state, loading, and mutating actions that refresh. */
export function useHostDashboardData({ isAdmin, pathname }) {
  const [analytics, setAnalytics] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [listings, setListings] = useState([]);
  const [hostListings, setHostListings] = useState([]);
  const [users, setUsers] = useState([]);
  const [kycQueue, setKycQueue] = useState([]);
  const [companyLocations, setCompanyLocations] = useState(EMPTY_LOCATIONS);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncingFleet, setIsSyncingFleet] = useState(false);
  const [bookingActionId, setBookingActionId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [connectStatus, setConnectStatus] = useState(null);
  const [recentPayouts, setRecentPayouts] = useState([]);

  const loadPayouts = useCallback(async () => {
    if (isAdmin) return null;
    try {
      const data = await apiGet("/api/payouts/connect/status", true);
      const connect = data?.connect || null;
      setConnectStatus(connect);
      setRecentPayouts(data?.recentPayouts || []);
      return connect;
    } catch (err) {
      const message = err?.message || "";
      if (/token|bearer|expired|unauthorized|missing bearer/i.test(message)) {
        setError("Session expired. Log in again to view payout status.");
      }
      setConnectStatus(null);
      setRecentPayouts([]);
      return null;
    }
  }, [isAdmin]);

  const loadAll = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      if (isAdmin) {
        const [analyticsRes, bookingsRes, listingsRes, hostListingsRes, usersRes, locationsRes, kycRes] =
          await Promise.all([
            apiGet("/api/analytics?scope=fleet", true),
            apiGet("/api/bookings?scope=fleet", true),
            apiGet("/api/listings?scope=fleet", true),
            apiGet("/api/listings?scope=host", true),
            apiGet("/api/users", true),
            apiGet("/api/company-locations", true),
            apiGet("/api/users/kyc?status=pending", true),
          ]);
        setAnalytics(analyticsRes?.analytics || null);
        setBookings(bookingsRes?.bookings || []);
        setListings(listingsRes?.listings || []);
        setHostListings(hostListingsRes?.listings || []);
        setUsers(usersRes?.users || []);
        setKycQueue(kycRes?.queue || []);
        setCompanyLocations({
          areas: locationsRes?.areas || [],
          branches: locationsRes?.branches || [],
          parkingSpots: locationsRes?.parkingSpots || [],
          vehicleClasses: locationsRes?.vehicleClasses || [],
        });
      } else {
        const [listingsRes, bookingsRes, analyticsRes, vehicleClassesRes] = await Promise.all([
          apiGet("/api/listings?scope=mine", true),
          apiGet("/api/bookings?scope=owner", true),
          apiGet("/api/analytics?scope=owner", true).catch(() => ({ analytics: null })),
          apiGet("/api/vehicle-classes", true).catch(() => ({ vehicleClasses: [] })),
        ]);
        setListings(listingsRes?.listings || []);
        setBookings(bookingsRes?.bookings || []);
        setAnalytics(analyticsRes?.analytics || null);
        setUsers([]);
        setCompanyLocations({
          ...EMPTY_LOCATIONS,
          vehicleClasses: vehicleClassesRes?.vehicleClasses || [],
        });
        await loadPayouts();
      }
    } catch (err) {
      setError(err?.message || `Could not load ${isAdmin ? "admin" : "host"} dashboard.`);
    } finally {
      setIsLoading(false);
    }
  }, [isAdmin, loadPayouts]);

  useEffect(() => {
    loadAll();
  }, [loadAll, pathname]);

  const deleteListing = async (listingId) => {
    if (
      !window.confirm(
        `Remove listing #${listingId}? It disappears from search; past trips are kept.`,
      )
    ) {
      return;
    }
    setError("");
    setSuccess("");
    try {
      await apiDelete(`/api/listings/${listingId}`, true);
      setSuccess("Listing removed.");
      await loadAll();
    } catch (err) {
      const message = err?.message || "Could not delete listing.";
      if (/not found/i.test(message)) {
        setSuccess("Listing already removed.");
        await loadAll();
        return;
      }
      setError(message);
    }
  };

  const setListingStatus = async (listingId, status) => {
    setError("");
    setSuccess("");
    try {
      await apiPatch(`/api/listings/${listingId}`, { status }, true);
      setSuccess(status === "ACTIVE" ? "Listing activated." : "Listing paused.");
      await loadAll();
    } catch (err) {
      setError(err?.message || "Could not update listing status.");
    }
  };

  const syncFleet = async () => {
    setError("");
    setSuccess("");
    setIsSyncingFleet(true);
    try {
      await apiPost("/api/fleet/sync", {}, true);
      setSuccess("Fleet synchronized.");
      await loadAll();
    } catch (err) {
      setError(err?.message || "Could not sync fleet.");
    } finally {
      setIsSyncingFleet(false);
    }
  };

  const handleBookingDecision = async (bookingId, action) => {
    setError("");
    setSuccess("");
    setBookingActionId(bookingId);
    const status = action === "approve" ? "CONFIRMED" : "CANCELLED";
    try {
      await apiPatch(`/api/bookings/${bookingId}`, { status }, true);
      setSuccess(
        action === "approve"
          ? "Booking approved."
          : action === "cancel"
            ? "Booking cancelled."
            : "Booking rejected.",
      );
      await loadAll();
    } catch (err) {
      setError(err?.message || `Could not ${action} booking.`);
    } finally {
      setBookingActionId(null);
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (!window.confirm("Cancel this booking? The guest will be notified.")) {
      return;
    }
    await handleBookingDecision(bookingId, "cancel");
  };

  const decideKyc = async (userId, verificationStatus) => {
    await apiPatch(`/api/users/${userId}/kyc`, { verificationStatus }, true);
    await loadAll();
  };

  return {
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
    setError,
    setSuccess,
    refresh: loadAll,
    deleteListing,
    setListingStatus,
    syncFleet,
    handleBookingDecision,
    handleCancelBooking,
    decideKyc,
    connectStatus,
    recentPayouts,
    refreshPayouts: loadPayouts,
  };
}
