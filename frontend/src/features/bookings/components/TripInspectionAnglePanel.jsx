import { Loader2 } from "lucide-react";
import AngleGuideFrame from "@/features/bookings/components/AngleGuideFrame";

export default function TripInspectionAnglePanel({
  slot,
  pending,
  inAlbum,
  isSkipped,
  canUpload,
  busyKey,
  onPick,
  onDiscard,
  onSave,
}) {
  const saveKey = `save-${slot.angleKey}`;

  if (pending) {
    return (
      <div className="relative mt-3 overflow-hidden rounded-2xl border-2 border-black bg-white">
        <img
          src={pending.previewUrl}
          alt="Preview"
          className="min-h-[180px] w-full object-cover"
        />
        <div className="flex gap-2 border-t-2 border-black bg-vroom-surface p-3">
          <button
            type="button"
            onClick={onDiscard}
            disabled={Boolean(busyKey)}
            className="flex-1 rounded-full border-2 border-black bg-white px-3 py-2 text-xs font-bold disabled:opacity-50"
          >
            Discard
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={busyKey === saveKey}
            className="inline-flex flex-1 items-center justify-center gap-1 rounded-full border-2 border-black bg-vroom-accent px-3 py-2 text-xs font-bold text-white disabled:opacity-50"
          >
            {busyKey === saveKey ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
            Add to album
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-3">
      {inAlbum && (
        <p className="mb-2 text-xs font-semibold text-emerald-700">In trip album — add another anytime</p>
      )}
      <AngleGuideFrame
        title={slot.title}
        instruction={slot.instruction}
        canUpload={canUpload}
        busyKey={busyKey}
        onPick={onPick}
        isSkipped={isSkipped}
      />
    </div>
  );
}
