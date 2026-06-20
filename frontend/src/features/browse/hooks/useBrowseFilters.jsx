import { createContext, useContext, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { apiGet } from "@/shared/api/api";
import FilterModal from "@/features/browse/components/FilterModal";
import {
  DEFAULT_FILTERS,
  FILTER_URL_KEYS,
  filtersActive,
  filtersToParams,
  parseFiltersFromSearchParams,
} from "@/features/browse/lib/filterParams";

const BrowseFiltersContext = createContext(null);

function copyFilters(filters) {
  return {
    ...filters,
    bodyTypeIds: [...filters.bodyTypeIds],
    fuelTypes: [...filters.fuelTypes],
    seats: [...filters.seats],
    featureIds: [...filters.featureIds],
  };
}

export function BrowseFiltersProvider({ children, searchContext }) {
  const [urlSearchParams, setUrlSearchParams] = useSearchParams();
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [draftFilters, setDraftFilters] = useState(DEFAULT_FILTERS);
  const [matchCount, setMatchCount] = useState(null);
  const [isCountLoading, setIsCountLoading] = useState(false);

  const appliedFilters = parseFiltersFromSearchParams(urlSearchParams);

  const openFilterModal = () => {
    setDraftFilters(copyFilters(appliedFilters));
    setIsFilterModalOpen(true);
  };

  const applyFilters = () => {
    const next = new URLSearchParams(urlSearchParams);
    FILTER_URL_KEYS.forEach((key) => next.delete(key));
    filtersToParams(draftFilters, { urlOnly: true }).forEach((value, key) => next.set(key, value));
    setUrlSearchParams(next, { replace: true });
    setIsFilterModalOpen(false);
  };

  const clearAllFilters = () => {
    setDraftFilters(copyFilters(DEFAULT_FILTERS));
    const next = new URLSearchParams(urlSearchParams);
    FILTER_URL_KEYS.forEach((key) => next.delete(key));
    setUrlSearchParams(next, { replace: true });
  };

  useEffect(() => {
    if (!isFilterModalOpen) return undefined;

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setIsCountLoading(true);
      try {
        const query = filtersToParams(draftFilters, { searchContext }).toString();
        const data = await apiGet(query ? `/api/listings/count?${query}` : "/api/listings/count");
        if (!cancelled) setMatchCount(Number(data?.totalCount ?? 0));
      } catch {
        if (!cancelled) setMatchCount(0);
      } finally {
        if (!cancelled) setIsCountLoading(false);
      }
    }, 400);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [draftFilters, isFilterModalOpen, searchContext]);

  const value = {
    appliedFilters,
    filtersActive: filtersActive(appliedFilters),
    openFilterModal,
  };

  return (
    <BrowseFiltersContext.Provider value={value}>
      {children}
      <FilterModal
        isOpen={isFilterModalOpen}
        onClose={() => setIsFilterModalOpen(false)}
        draft={draftFilters}
        onChange={setDraftFilters}
        count={matchCount}
        isCountLoading={isCountLoading}
        onApply={applyFilters}
        onClearAll={clearAllFilters}
      />
    </BrowseFiltersContext.Provider>
  );
}

export function useBrowseFilters() {
  const context = useContext(BrowseFiltersContext);
  if (!context) {
    throw new Error("useBrowseFilters must be used within BrowseFiltersProvider");
  }
  return context;
}

export function useOptionalBrowseFilters() {
  return useContext(BrowseFiltersContext);
}
