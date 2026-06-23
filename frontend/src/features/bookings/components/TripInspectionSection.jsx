import { forwardRef, useCallback, useEffect, useId, useImperativeHandle, useState } from "react";
import { ChevronDown, Loader2 } from "lucide-react";
import { apiGet } from "@/shared/api/api";
import TripInspectionWizard from "@/features/bookings/components/TripInspectionWizard";
import HostInspectionCompare from "@/features/bookings/components/HostInspectionCompare";
import {
  countRecommendedUploaded,
  flattenStandardSlots,
} from "@/features/bookings/lib/tripInspectionLinearSteps";

const TripInspectionSection = forwardRef(function TripInspectionSection(
  {
    bookingId,
    isRenter,
    isHost,
    canUploadCheckIn,
    canUploadCheckOut,
    showPickupNudge,
    showReturnNudge,
    onRecommendedComplete,
    onExteriorComplete,
  },
  ref,
) {
  const sectionId = useId().replace(/:/g, "");
  const [expanded, setExpanded] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);

  const browseOnly = isHost && !isRenter;
  const canUpload = isRenter && (canUploadCheckIn || canUploadCheckOut);

  const load = useCallback(async () => {
    setError("");
    setIsLoading(true);
    try {
      const result = await apiGet(`/api/bookings/${bookingId}/inspection`, true);
      setData(result);
      setHasFetched(true);
      return result;
    } catch (err) {
      setData(null);
      setError(err?.message || "Could not load inspection photos.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [bookingId]);

  const openInspection = useCallback(async () => {
    setExpanded(true);
    if (!data) await load();
    window.requestAnimationFrame(() => {
      document.getElementById(`trip-inspection-${sectionId}`)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }, [data, load, sectionId]);

  useImperativeHandle(ref, () => ({ openInspection }));

  useEffect(() => {
    if (expanded && !hasFetched && !isLoading) {
      load();
    }
  }, [expanded, hasFetched, isLoading, load]);

  useEffect(() => {
    if (!data?.checkIn || !onRecommendedComplete) return;
    const flat = flattenStandardSlots(data.checkIn);
    if (countRecommendedUploaded(flat) >= 8) {
      onRecommendedComplete();
    }
  }, [data, onRecommendedComplete]);

  const checkInCount = data?.checkIn?.uploaded ?? 0;
  const checkOutCount = data?.checkOut?.uploaded ?? 0;
  const summary =
    hasFetched || data
      ? `Check-in ${checkInCount} · Check-out ${checkOutCount}`
      : "Tap to view vehicle photos";

  const handlePrimaryCta = async () => {
    if (browseOnly || canUpload) {
      await openInspection();
      return;
    }
    setExpanded((current) => !current);
  };

  return (
    <section
      id={`trip-inspection-${sectionId}`}
      className="rounded-3xl border-2 border-black bg-vroom-surface p-4 shadow-neoCard"
    >
      <div className="flex items-start justify-between gap-3">
        <button
          type="button"
          onClick={() => setExpanded((current) => !current)}
          className="min-w-0 flex-1 text-left"
          aria-expanded={expanded}
        >
          <h2 className="text-lg font-extrabold text-vroom-heading">Vehicle condition photos</h2>
          <p className="mt-0.5 text-xs text-gray-600">{summary}</p>
        </button>
        <ChevronDown
          className={`h-5 w-5 shrink-0 text-vroom-heading transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </div>

      <div className="mt-3">
        <button
          type="button"
          onClick={handlePrimaryCta}
          className="w-full rounded-full border-2 border-black bg-vroom-accent px-4 py-2 text-sm font-extrabold text-white shadow-neoSm"
        >
          {browseOnly ? "View photos" : canUpload ? "Start inspection" : "View photos"}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3">
          {showPickupNudge && isRenter && (
            <p className="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
              Recommended: document vehicle condition before pickup.
            </p>
          )}
          {showReturnNudge && isRenter && (
            <p className="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
              Recommended: document vehicle condition before return.
            </p>
          )}

          {isLoading && !data && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading vehicle photos...
            </div>
          )}

          {error && !data && <p className="text-sm text-red-600">{error}</p>}

          {data && browseOnly && <HostInspectionCompare data={data} />}

          {data && !browseOnly && (
            <TripInspectionWizard
              bookingId={bookingId}
              data={data}
              onRefresh={load}
              isRenter={isRenter}
              canUploadCheckIn={canUploadCheckIn}
              canUploadCheckOut={canUploadCheckOut}
              onRecommendedComplete={onRecommendedComplete}
              onExteriorComplete={onExteriorComplete}
            />
          )}

          {error && data && <p className="text-sm text-red-600">{error}</p>}
        </div>
      )}
    </section>
  );
});

export default TripInspectionSection;
