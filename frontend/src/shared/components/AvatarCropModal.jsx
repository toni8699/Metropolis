import { useCallback, useState } from "react";
import Cropper from "react-easy-crop";
import { Loader2, X } from "lucide-react";
import { getCroppedImageBlob } from "@/shared/lib/cropImage";

export default function AvatarCropModal({
  isOpen,
  imageSrc,
  onCancel,
  onApply,
  isApplying = false,
}) {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState(null);
  const [error, setError] = useState("");

  const onCropComplete = useCallback((_croppedArea, pixels) => {
    setCroppedAreaPixels(pixels);
  }, []);

  const handleApply = async () => {
    if (!croppedAreaPixels) {
      setError("Adjust the crop area before applying.");
      return;
    }
    setError("");
    try {
      const blob = await getCroppedImageBlob(imageSrc, croppedAreaPixels);
      const file = new File([blob], "avatar.jpg", { type: "image/jpeg" });
      await onApply(file);
    } catch (err) {
      setError(err?.message || "Could not crop image.");
    }
  };

  if (!isOpen || !imageSrc) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="avatar-crop-title"
    >
      <div className="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <h2 id="avatar-crop-title" className="text-lg font-semibold text-gray-900">
            Crop profile photo
          </h2>
          <button
            type="button"
            onClick={onCancel}
            disabled={isApplying}
            className="rounded-full p-1 text-gray-500 hover:bg-gray-100 disabled:opacity-40"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="relative h-64 w-full bg-gray-900">
          <Cropper
            image={imageSrc}
            crop={crop}
            zoom={zoom}
            aspect={1}
            cropShape="round"
            showGrid={false}
            onCropChange={setCrop}
            onZoomChange={setZoom}
            onCropComplete={onCropComplete}
          />
        </div>

        <div className="space-y-4 px-5 py-4">
          <div>
            <label htmlFor="avatar-crop-zoom" className="text-sm font-medium text-gray-700">
              Zoom
            </label>
            <input
              id="avatar-crop-zoom"
              type="range"
              min={1}
              max={3}
              step={0.05}
              value={zoom}
              onChange={(event) => setZoom(Number(event.target.value))}
              disabled={isApplying}
              className="mt-2 h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-indigo-600 disabled:opacity-40"
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onCancel}
              disabled={isApplying}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleApply}
              disabled={isApplying}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isApplying && <Loader2 className="h-4 w-4 animate-spin" />}
              {isApplying ? "Uploading..." : "Apply"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
