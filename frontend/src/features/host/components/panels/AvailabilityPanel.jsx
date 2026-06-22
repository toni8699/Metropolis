import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";
import { LabeledSelect } from "@/features/host/components/form/Fields";
import { apiDelete, apiGet, apiPost } from "@/shared/api/api";
import { bookingWindowFromDateStrings, dateRangeOverlapsBooked } from "@/shared/lib/bookingDates";
import {
  airbnbDayPickerClassNames,
  bookedDayModifierClassNames,
  buildBookedModifiers,
  buildHostBlockedModifiers,
  buildListingDatePickerDisabled,
  hostBlockedDayModifierClassNames,
  sanitizeDateRange,
  startOfToday,
} from "@/shared/lib/datePicker";

function formatRangeLabel(startAt, endAt) {
  const from = format(new Date(startAt), "MMM d, yyyy");
  const to = format(new Date(endAt), "MMM d, yyyy");
  return `${from} → ${to}`;
}

export default function AvailabilityPanel({ listings }) {
  const activeListings = useMemo(
    () => (listings || []).filter((listing) => listing.active !== false),
    [listings],
  );

  const [listingId, setListingId] = useState("");
  const [blockedRanges, setBlockedRanges] = useState([]);
  const [bookedRanges, setBookedRanges] = useState([]);
  const [dateRange, setDateRange] = useState({ from: undefined, to: undefined });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [removingId, setRemovingId] = useState(null);
  const [error, setError] = useState("");

  const listingOptions = useMemo(
    () =>
      activeListings.map((listing) => ({
        value: String(listing.listingId),
        label: listing.listingTitle || listing.title || `Listing #${listing.listingId}`,
      })),
    [activeListings],
  );

  const selectedId = Number(listingId) || null;

  const loadCalendarData = useCallback(async (id) => {
    if (!id) {
      setBlockedRanges([]);
      setBookedRanges([]);
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const [blockedData, bookedData] = await Promise.all([
        apiGet(`/api/listings/${id}/availability`, true),
        apiGet(`/api/listings/${id}/booked-ranges`),
      ]);
      setBlockedRanges(blockedData?.availability || []);
      setBookedRanges(bookedData?.ranges || []);
    } catch (err) {
      setError(err?.message || "Could not load calendar.");
      setBlockedRanges([]);
      setBookedRanges([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedId && activeListings.length === 1) {
      setListingId(String(activeListings[0].listingId));
      return;
    }
    loadCalendarData(selectedId);
    setDateRange({ from: undefined, to: undefined });
  }, [selectedId, activeListings, loadCalendarData]);

  const calendarDisabled = useMemo(
    () => buildListingDatePickerDisabled(bookedRanges),
    [bookedRanges],
  );

  const calendarModifiers = useMemo(
    () => ({
      ...buildBookedModifiers(bookedRanges),
      ...buildHostBlockedModifiers(blockedRanges),
    }),
    [bookedRanges, blockedRanges],
  );

  const calendarModifierClassNames = useMemo(
    () => ({
      ...bookedDayModifierClassNames,
      ...hostBlockedDayModifierClassNames,
    }),
    [],
  );

  const hasCompleteRange = Boolean(dateRange.from && dateRange.to);

  const blockDates = useCallback(async () => {
    if (!selectedId || !hasCompleteRange) {
      return;
    }
    if (dateRangeOverlapsBooked(dateRange.from, dateRange.to, bookedRanges)) {
      setError("Selected dates overlap an existing booking.");
      return;
    }

    setIsSaving(true);
    setError("");
    try {
      const window = bookingWindowFromDateStrings(
        format(dateRange.from, "yyyy-MM-dd"),
        format(dateRange.to, "yyyy-MM-dd"),
      );
      await apiPost(
        `/api/listings/${selectedId}/availability`,
        { ...window, status: "BLOCKED" },
        true,
      );
      setDateRange({ from: undefined, to: undefined });
      await loadCalendarData(selectedId);
    } catch (err) {
      setError(err?.message || "Could not block dates.");
    } finally {
      setIsSaving(false);
    }
  }, [selectedId, hasCompleteRange, dateRange, bookedRanges, loadCalendarData]);

  const removeBlock = useCallback(
    async (availabilityId) => {
      if (!selectedId) {
        return;
      }
      setRemovingId(availabilityId);
      setError("");
      try {
        await apiDelete(`/api/listings/${selectedId}/availability/${availabilityId}`, true);
        await loadCalendarData(selectedId);
      } catch (err) {
        setError(err?.message || "Could not remove block.");
      } finally {
        setRemovingId(null);
      }
    },
    [selectedId, loadCalendarData],
  );

  if (activeListings.length === 0) {
    return (
      <section className="mx-11 mt-6 rounded-2xl border-2 border-black bg-white p-6">
        <h2 className="text-xl font-extrabold text-vroom-heading">Availability</h2>
        <p className="mt-2 text-sm text-vroom-muted">
          Create a listing first, then block dates when the car is unavailable.
        </p>
      </section>
    );
  }

  return (
    <section className="mx-11 mt-6 space-y-6">
      <div className="rounded-2xl border-2 border-black bg-white p-6">
        <h2 className="text-xl font-extrabold text-vroom-heading">Block dates</h2>
        <p className="mt-2 text-sm text-vroom-muted">
          Pick a listing and date range. Blocked days drop out of search. Booked trips stay locked.
        </p>

        <div className="mt-4 max-w-md">
          <LabeledSelect
            label="Listing"
            value={listingId}
            onChange={setListingId}
            options={listingOptions}
            placeholder="Select listing"
          />
        </div>

        {selectedId && (
          <>
            <div className="mt-6 inline-block rounded-2xl border-2 border-black bg-vroom-card p-6 shadow-neo">
              {isLoading ? (
                <p className="text-sm text-vroom-muted">Loading calendar...</p>
              ) : (
                <DayPicker
                  mode="range"
                  numberOfMonths={2}
                  startMonth={startOfToday()}
                  disabled={calendarDisabled}
                  modifiers={calendarModifiers}
                  modifiersClassNames={calendarModifierClassNames}
                  selected={dateRange}
                  onSelect={(range) => {
                    const next = sanitizeDateRange(range);
                    if (dateRangeOverlapsBooked(next.from, next.to, bookedRanges)) {
                      return;
                    }
                    setDateRange(next);
                  }}
                  className="rdp-airbnb"
                  classNames={airbnbDayPickerClassNames()}
                  components={{
                    Chevron: ({ orientation, ...props }) =>
                      orientation === "left" ? (
                        <ChevronLeft {...props} className="h-5 w-5" />
                      ) : (
                        <ChevronRight {...props} className="h-5 w-5" />
                      ),
                  }}
                />
              )}
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-gray-600">
              <span className="inline-flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full bg-amber-100 ring-1 ring-amber-500" />
                Your blocks
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full bg-gray-200 line-through">12</span>
                Booked
              </span>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={blockDates}
                disabled={!hasCompleteRange || isSaving || isLoading}
                className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {isSaving ? "Saving..." : "Block selected dates"}
              </button>
              {hasCompleteRange && (
                <p className="text-sm text-gray-600">
                  {format(dateRange.from, "MMM d")} – {format(dateRange.to, "MMM d, yyyy")}
                </p>
              )}
            </div>
          </>
        )}

        {error && <p className="mt-3 text-sm font-semibold text-red-700">{error}</p>}
      </div>

      {selectedId && blockedRanges.length > 0 && (
        <div className="rounded-2xl border-2 border-black bg-white p-6">
          <h3 className="text-lg font-extrabold text-vroom-heading">Blocked windows</h3>
          <ul className="mt-4 divide-y divide-gray-200">
            {blockedRanges.map((block) => (
              <li
                key={block.availabilityId}
                className="flex flex-wrap items-center justify-between gap-2 py-3"
              >
                <p className="font-semibold text-gray-900">
                  {formatRangeLabel(block.startAt, block.endAt)}
                </p>
                <button
                  type="button"
                  onClick={() => removeBlock(block.availabilityId)}
                  disabled={removingId === block.availabilityId}
                  className="text-sm font-semibold text-red-600 hover:underline disabled:opacity-50"
                >
                  {removingId === block.availabilityId ? "Removing..." : "Remove"}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
