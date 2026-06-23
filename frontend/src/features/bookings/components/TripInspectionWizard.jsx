import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { compressTripPhoto } from "@/shared/lib/compressTripPhoto";
import TripInspectionAnglePanel from "@/features/bookings/components/TripInspectionAnglePanel";
import TripInspectionMilestoneBar from "@/features/bookings/components/TripInspectionMilestoneBar";
import TripPhotosAlbum from "@/features/bookings/components/TripPhotosAlbum";
import { deleteTripInspectionPhoto } from "@/features/bookings/lib/deleteTripInspectionPhoto";
import { uploadTripInspectionPhoto } from "@/features/bookings/lib/uploadTripInspectionPhoto";
import {
  countRecommendedUploaded,
  findResumeStepIndex,
  firstStepIndexForGroup,
  flattenStandardSlots,
  getStepMeta,
  groupMilestoneCounts,
  isLastStepInGroup,
} from "@/features/bookings/lib/tripInspectionLinearSteps";
import { collectPhasePhotos } from "@/features/bookings/lib/tripInspectionPhotos";
import { useTripInspectionUploadQueue } from "@/features/bookings/hooks/useTripInspectionUploadQueue";

export default function TripInspectionWizard({
  bookingId,
  data,
  onRefresh,
  isRenter,
  canUploadCheckIn,
  canUploadCheckOut,
  browseOnly = false,
  onExteriorComplete,
  onRecommendedComplete,
}) {
  const [phase, setPhase] = useState("checkIn");
  const [stepIndex, setStepIndex] = useState(0);
  const [skippedKeys, setSkippedKeys] = useState(() => new Set());
  const [pending, setPending] = useState(null);
  const [error, setError] = useState("");
  const [busyKey, setBusyKey] = useState(null);
  const [pulseGroupKey, setPulseGroupKey] = useState(null);
  const [exteriorCompleteMsg, setExteriorCompleteMsg] = useState(false);
  const fileInputRef = useRef(null);
  const pickTargetRef = useRef(null);
  const refreshTimerRef = useRef(null);

  const checkIn = data?.checkIn || { slots: [], uploaded: 0, canUpload: false };
  const checkOut = data?.checkOut || { slots: [], uploaded: 0, canUpload: false };
  const activePhase = phase === "checkIn" ? checkIn : checkOut;
  const phaseKey = phase === "checkIn" ? "CHECK_IN" : "CHECK_OUT";
  const canUpload =
    !browseOnly &&
    isRenter &&
    (phase === "checkIn" ? canUploadCheckIn : canUploadCheckOut) &&
    activePhase.canUpload;
  const purged = Boolean(data?.purged);

  const flatSlots = useMemo(() => flattenStandardSlots(activePhase), [activePhase]);
  const activeSlot = flatSlots[stepIndex] || null;
  const stepMeta = activeSlot ? getStepMeta(stepIndex, flatSlots) : null;
  const milestones = useMemo(() => groupMilestoneCounts(flatSlots), [flatSlots]);
  const standardUploaded = activePhase.standardUploaded ?? activePhase.uploaded ?? 0;
  const standardTotal = activePhase.standardTotal || flatSlots.length || 16;
  const albumPhotos = useMemo(() => collectPhasePhotos(activePhase), [activePhase]);

  const debouncedRefresh = useCallback(() => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    refreshTimerRef.current = setTimeout(() => onRefresh?.(), 400);
  }, [onRefresh]);

  const {
    enqueue,
    retry,
    getJobsForPhase,
    clearJobForAngle,
    finalizeJob,
    pendingCount,
  } = useTripInspectionUploadQueue({
    bookingId: Number(bookingId),
    onJobDone: debouncedRefresh,
    onJobFailed: (job) => setError(job.error || "Upload failed."),
  });

  const queueJobs = getJobsForPhase(phaseKey);

  useEffect(() => () => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
  }, []);

  useEffect(() => {
    if (!pending?.previewUrl) return undefined;
    return () => URL.revokeObjectURL(pending.previewUrl);
  }, [pending?.previewUrl]);

  useEffect(() => {
    flatSlots.forEach((slot) => {
      if (slot.photo?.fileUrl) {
        finalizeJob(slot.angleKey, phaseKey);
      }
    });
  }, [flatSlots, phaseKey, finalizeJob]);

  useEffect(() => {
    if (flatSlots.length === 0) return;
    setStepIndex(findResumeStepIndex(flatSlots));
  }, [phase]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (phase !== "checkIn" || flatSlots.length === 0) return;
    const recommended = countRecommendedUploaded(flatSlots);
    if (recommended >= 8) {
      onRecommendedComplete?.();
      if (!exteriorCompleteMsg) setExteriorCompleteMsg(true);
    }
    const exterior = milestones.find((m) => m.key === "exterior");
    if (exterior && exterior.uploaded >= exterior.total && exterior.total > 0) {
      onExteriorComplete?.();
    }
  }, [
    phase,
    flatSlots,
    milestones,
    exteriorCompleteMsg,
    onExteriorComplete,
    onRecommendedComplete,
  ]);

  const clearPending = useCallback(() => {
    setPending((current) => {
      if (current?.previewUrl) URL.revokeObjectURL(current.previewUrl);
      return null;
    });
  }, []);

  const dismissPending = useCallback(() => {
    setPending(null);
  }, []);

  const switchPhase = (nextPhase) => {
    clearPending();
    setPhase(nextPhase);
    setSkippedKeys(new Set());
    setStepIndex(0);
    setError("");
    setPulseGroupKey(null);
    setExteriorCompleteMsg(false);
  };

  const pulseGroup = (groupKey) => {
    setPulseGroupKey(groupKey);
    window.setTimeout(() => setPulseGroupKey(null), 300);
  };

  const advanceStep = useCallback(
    (fromIndex) => {
      const idx = fromIndex ?? stepIndex;
      if (idx < flatSlots.length - 1) {
        const nextIndex = idx + 1;
        const currentMeta = getStepMeta(idx, flatSlots);
        const nextMeta = getStepMeta(nextIndex, flatSlots);
        if (currentMeta.groupKey !== nextMeta.groupKey) {
          pulseGroup(nextMeta.groupKey);
        }
        setStepIndex(nextIndex);
      }
    },
    [flatSlots, stepIndex],
  );

  const goPrev = () => {
    clearPending();
    setStepIndex((current) => Math.max(0, current - 1));
  };

  const goNext = () => {
    clearPending();
    if (stepIndex < flatSlots.length - 1) advanceStep(stepIndex);
  };

  const skipCurrent = useCallback(() => {
    if (!activeSlot || !canUpload) return;
    setSkippedKeys((current) => new Set(current).add(activeSlot.angleKey));
    clearPending();
    advanceStep(stepIndex);
  }, [activeSlot, canUpload, advanceStep, stepIndex, clearPending]);

  const selectGroup = (groupKey) => {
    clearPending();
    setStepIndex(firstStepIndexForGroup(flatSlots, groupKey));
    setPulseGroupKey(null);
  };

  const startPick = useCallback((target) => {
    pickTargetRef.current = target;
    fileInputRef.current?.click();
  }, []);

  const handleFilePick = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    const target = pickTargetRef.current;
    pickTargetRef.current = null;
    if (!file || !target) return;

    setError("");
    setBusyKey("pick");
    try {
      const compressed = await compressTripPhoto(file);
      clearPending();
      const previewUrl = URL.createObjectURL(compressed);
      setPending({ file: compressed, previewUrl, target });
      if (target.angleKey) {
        setSkippedKeys((current) => {
          if (!current.has(target.angleKey)) return current;
          const next = new Set(current);
          next.delete(target.angleKey);
          return next;
        });
      }
    } catch (err) {
      setError(err?.message || "Could not process photo.");
    } finally {
      setBusyKey(null);
    }
  };

  const handleSavePending = async () => {
    if (!pending) return;
    const { file, target } = pending;
    const previewUrl = pending.previewUrl;

    if (target.isExtra) {
      const actionKey = `extra-save-${target.replacePhotoId || "new"}`;
      setBusyKey(actionKey);
      setError("");
      try {
        if (target.replacePhotoId) {
          await deleteTripInspectionPhoto(bookingId, target.replacePhotoId);
        }
        await uploadTripInspectionPhoto(file, {
          bookingId: Number(bookingId),
          phase: phaseKey,
          isExtra: true,
          skipCompress: true,
        });
        URL.revokeObjectURL(previewUrl);
        dismissPending();
        await onRefresh();
      } catch (err) {
        setError(err?.message || "Upload failed.");
      } finally {
        setBusyKey(null);
      }
      return;
    }

    const angleKey = target.angleKey;
    const label = flatSlots.find((s) => s.angleKey === angleKey)?.title || "Photo";
    dismissPending();
    setSkippedKeys((current) => {
      const next = new Set(current);
      next.delete(angleKey);
      return next;
    });

    enqueue({
      angleKey,
      file,
      phase: phaseKey,
      localPreviewUrl: previewUrl,
      replacePhotoId: target.replacePhotoId,
      label,
    });
    advanceStep(stepIndex);
  };

  const handleDeletePhoto = async (photo) => {
    const key = `delete-${photo.photoId}`;
    setBusyKey(key);
    setError("");
    try {
      if (photo.angleKey) clearJobForAngle(photo.angleKey, phaseKey);
      await deleteTripInspectionPhoto(bookingId, photo.photoId);
      clearPending();
      await onRefresh();
    } catch (err) {
      setError(err?.message || "Delete failed.");
    } finally {
      setBusyKey(null);
    }
  };

  if (purged) {
    return <p className="text-sm text-gray-600">Inspection photos expired.</p>;
  }

  return (
    <div className="space-y-4">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFilePick}
      />

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => switchPhase("checkIn")}
          className={`rounded-full border-2 border-black px-3 py-1 text-xs font-bold ${
            phase === "checkIn" ? "bg-vroom-heading text-white" : "bg-white"
          }`}
        >
          Check-in ({checkIn.uploaded || 0})
        </button>
        <button
          type="button"
          onClick={() => switchPhase("checkOut")}
          className={`rounded-full border-2 border-black px-3 py-1 text-xs font-bold ${
            phase === "checkOut" ? "bg-vroom-heading text-white" : "bg-white"
          }`}
        >
          Check-out ({checkOut.uploaded || 0})
        </button>
      </div>

      {exteriorCompleteMsg && phase === "checkIn" && (
        <p className="rounded-xl border border-emerald-400 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-900">
          Exterior done — you can confirm pickup anytime.
        </p>
      )}

      {!canUpload && isRenter && !browseOnly && (
        <p className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
          {phase === "checkIn"
            ? "Check-in photos only during confirmed trip window."
            : "Check-out photos only while trip is in progress."}
        </p>
      )}

      <TripPhotosAlbum
        photos={albumPhotos}
        queueJobs={queueJobs}
        canUpload={canUpload}
        busyKey={busyKey}
        onAddPhoto={() => startPick({ type: "extra", isExtra: true })}
        onDelete={handleDeletePhoto}
        onRetry={retry}
      />

      {pending?.target?.isExtra && (
        <div className="overflow-hidden rounded-2xl border-2 border-black bg-white">
          <img
            src={pending.previewUrl}
            alt="Preview"
            className="max-h-48 w-full object-cover"
          />
          <div className="flex gap-2 border-t-2 border-black bg-vroom-surface p-3">
            <button
              type="button"
              onClick={clearPending}
              className="flex-1 rounded-full border-2 border-black bg-white px-3 py-2 text-xs font-bold"
            >
              Discard
            </button>
            <button
              type="button"
              onClick={handleSavePending}
              disabled={busyKey?.startsWith("extra-save")}
              className="flex-1 rounded-full border-2 border-black bg-vroom-accent px-3 py-2 text-xs font-bold text-white disabled:opacity-50"
            >
              Add to album
            </button>
          </div>
        </div>
      )}

      <p className="text-xs text-gray-500">
        {standardUploaded} / {standardTotal} suggested shots · All photos optional
      </p>

      {activeSlot && canUpload && (
        <div className="overflow-hidden rounded-2xl border-2 border-black bg-white p-4 shadow-neoSm">
          <TripInspectionMilestoneBar
            milestones={milestones}
            activeGroupKey={stepMeta?.groupKey}
            pulseGroupKey={pulseGroupKey}
            onSelectGroup={selectGroup}
          />

          <p className="mt-4 text-xs font-semibold text-gray-500">
            Suggested shot {stepMeta.globalIndex + 1} of {stepMeta.globalTotal}
            {activeSlot.recommendedFirst ? " · Priority" : ""}
          </p>

          <TripInspectionAnglePanel
            slot={activeSlot}
            pending={
              pending?.target?.type === "standard" &&
              pending.target.angleKey === activeSlot.angleKey
                ? pending
                : null
            }
            inAlbum={Boolean(activeSlot.photo?.fileUrl)}
            isSkipped={skippedKeys.has(activeSlot.angleKey)}
            canUpload={canUpload}
            busyKey={busyKey}
            onPick={() =>
              startPick({
                type: "standard",
                angleKey: activeSlot.angleKey,
                isExtra: false,
                replacePhotoId: activeSlot.photo?.photoId,
              })
            }
            onDiscard={clearPending}
            onSave={handleSavePending}
          />

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
            <button
              type="button"
              onClick={goPrev}
              disabled={stepIndex === 0}
              className="inline-flex items-center gap-1 rounded-full border-2 border-black bg-white px-3 py-1.5 text-xs font-bold disabled:opacity-40"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Prev
            </button>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={skipCurrent}
                disabled={Boolean(busyKey)}
                className="rounded-full border-2 border-black bg-white px-3 py-1.5 text-xs font-bold disabled:opacity-50"
              >
                Skip
              </button>
              <button
                type="button"
                onClick={goNext}
                disabled={stepIndex >= flatSlots.length - 1}
                className="inline-flex items-center gap-1 rounded-full border-2 border-black bg-vroom-sage px-3 py-1.5 text-xs font-bold disabled:opacity-40"
              >
                {isLastStepInGroup(stepIndex, flatSlots) && stepIndex < flatSlots.length - 1
                  ? "Next group"
                  : "Next"}
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {pendingCount > 0 && (
        <p className="text-xs text-gray-500">{pendingCount} photo(s) still uploading…</p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
