import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { buildGroupedPhase } from "@/features/bookings/lib/tripInspectionGroups";
import { flattenStandardSlots } from "@/features/bookings/lib/tripInspectionLinearSteps";

function buildCompareRows(checkIn, checkOut) {
  const checkInFlat = flattenStandardSlots(checkIn);
  const checkOutFlat = flattenStandardSlots(checkOut);
  const checkOutByKey = new Map(checkOutFlat.map((slot) => [slot.angleKey, slot]));

  return checkInFlat.map((slot) => ({
    angleKey: slot.angleKey,
    title: slot.title,
    instruction: slot.instruction,
    checkInPhoto: slot.photo,
    checkOutPhoto: checkOutByKey.get(slot.angleKey)?.photo || null,
  }));
}

function PhotoThumb({ photo, label, variant, onClick }) {
  const borderClass =
    variant === "checkIn"
      ? "border-emerald-600"
      : photo?.fileUrl
        ? "border-black"
        : "border-amber-500";

  if (!photo?.fileUrl) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`flex min-h-[120px] w-full flex-col items-center justify-center rounded-xl border-2 border-dashed ${borderClass} bg-gray-50 text-xs text-gray-500`}
      >
        <span className="font-bold text-gray-700">{label}</span>
        <span className="mt-1">No photo</span>
      </button>
    );
  }

  return (
    <button type="button" onClick={onClick} className="block w-full text-left">
      <p className="mb-1 text-[10px] font-bold uppercase text-gray-600">{label}</p>
      <img
        src={photo.fileUrl}
        alt={label}
        className={`min-h-[120px] w-full rounded-xl border-2 ${borderClass} object-cover`}
      />
    </button>
  );
}

function Lightbox({ src, title, onClose }) {
  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-[140] flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div className="relative max-h-full max-w-3xl" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          onClick={onClose}
          className="absolute -right-2 -top-2 rounded-full border-2 border-black bg-white p-1"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
        <img src={src} alt={title} className="max-h-[85vh] rounded-xl border-2 border-black" />
        <p className="mt-2 text-center text-sm font-bold text-white">{title}</p>
      </div>
    </div>
  );
}

function ExtrasStrip({ label, extras }) {
  if (!extras.length) return null;
  return (
    <div className="space-y-2">
      <p className="text-xs font-extrabold text-vroom-heading">{label}</p>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {extras.map((slot) => (
          <img
            key={slot.photo?.photoId || slot.angleKey}
            src={slot.photo?.fileUrl}
            alt="Damage close-up"
            className="h-24 w-24 shrink-0 rounded-lg border-2 border-black object-cover"
          />
        ))}
      </div>
    </div>
  );
}

export default function HostInspectionCompare({ data }) {
  const [lightbox, setLightbox] = useState(null);

  const checkIn = data?.checkIn || { slots: [] };
  const checkOut = data?.checkOut || { slots: [] };
  const purged = Boolean(data?.purged);

  const rows = useMemo(() => buildCompareRows(checkIn, checkOut), [checkIn, checkOut]);
  const checkInExtras = useMemo(() => buildGroupedPhase(checkIn).extras, [checkIn]);
  const checkOutExtras = useMemo(() => buildGroupedPhase(checkOut).extras, [checkOut]);

  if (purged) {
    return <p className="text-sm text-gray-600">Inspection photos expired.</p>;
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-600">
        Compare check-in and check-out photos side by side for each angle.
      </p>
      {data?.expiresAt ? (
        <p className="text-xs text-gray-500">
          Photos kept until {new Date(data.expiresAt).toLocaleDateString()}.
        </p>
      ) : null}

      <div className="space-y-4">
        {rows.map((row) => (
          <div
            key={row.angleKey}
            className="rounded-2xl border-2 border-black bg-white p-3 shadow-neoSm"
          >
            <p className="text-sm font-extrabold text-vroom-heading">{row.title}</p>
            <p className="mt-0.5 text-xs text-gray-600">{row.instruction}</p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <PhotoThumb
                photo={row.checkInPhoto}
                label="Check-in"
                variant="checkIn"
                onClick={() =>
                  row.checkInPhoto?.fileUrl &&
                  setLightbox({ src: row.checkInPhoto.fileUrl, title: `${row.title} — Check-in` })
                }
              />
              <PhotoThumb
                photo={row.checkOutPhoto}
                label="Check-out"
                variant="checkOut"
                onClick={() =>
                  row.checkOutPhoto?.fileUrl &&
                  setLightbox({
                    src: row.checkOutPhoto.fileUrl,
                    title: `${row.title} — Check-out`,
                  })
                }
              />
            </div>
          </div>
        ))}
      </div>

      {(checkInExtras.length > 0 || checkOutExtras.length > 0) && (
        <div className="space-y-3 border-t border-gray-200 pt-4">
          <p className="text-sm font-extrabold text-vroom-heading">Damage close-ups</p>
          <ExtrasStrip label="Check-in" extras={checkInExtras} />
          <ExtrasStrip label="Check-out" extras={checkOutExtras} />
        </div>
      )}

      {lightbox && (
        <Lightbox src={lightbox.src} title={lightbox.title} onClose={() => setLightbox(null)} />
      )}
    </div>
  );
}
