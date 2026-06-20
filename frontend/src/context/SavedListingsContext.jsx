import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPost } from "@/shared/api/api";

const SavedListingsContext = createContext(null);

export function SavedListingsProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [savedIds, setSavedIds] = useState(() => new Set());
  const [isLoading, setIsLoading] = useState(false);

  const refreshSaved = useCallback(async () => {
    if (!isAuthenticated) {
      setSavedIds(new Set());
      return;
    }
    setIsLoading(true);
    try {
      const data = await apiGet("/api/me/saved-listings", true);
      setSavedIds(new Set((data?.savedListingIds || []).map(Number)));
    } catch {
      setSavedIds(new Set());
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshSaved();
  }, [refreshSaved]);

  const isSaved = useCallback(
    (listingId) => savedIds.has(Number(listingId)),
    [savedIds],
  );

  const toggleSaved = useCallback(
    async (listingId) => {
      const id = Number(listingId);
      const wasSaved = savedIds.has(id);
      setSavedIds((prev) => {
        const next = new Set(prev);
        if (wasSaved) {
          next.delete(id);
        } else {
          next.add(id);
        }
        return next;
      });
      try {
        if (wasSaved) {
          await apiDelete(`/api/me/saved-listings/${id}`, true);
        } else {
          await apiPost(`/api/me/saved-listings/${id}`, {}, true);
        }
      } catch (err) {
        setSavedIds((prev) => {
          const next = new Set(prev);
          if (wasSaved) {
            next.add(id);
          } else {
            next.delete(id);
          }
          return next;
        });
        throw err;
      }
    },
    [savedIds],
  );

  const value = useMemo(
    () => ({
      savedIds,
      isLoading,
      isSaved,
      toggleSaved,
      refreshSaved,
    }),
    [savedIds, isLoading, isSaved, toggleSaved, refreshSaved],
  );

  return (
    <SavedListingsContext.Provider value={value}>{children}</SavedListingsContext.Provider>
  );
}

export function useSavedListings() {
  const context = useContext(SavedListingsContext);
  if (!context) {
    throw new Error("useSavedListings must be used within SavedListingsProvider");
  }
  return context;
}

export function useOptionalSavedListings() {
  return useContext(SavedListingsContext);
}
