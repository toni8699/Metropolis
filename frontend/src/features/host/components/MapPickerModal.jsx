import { X } from "lucide-react";
import MapPinPicker from "@/features/host/components/MapPinPicker";

export default function MapPickerModal({
  apiKey,
  isMapLoaded,
  tempLocation,
  isReverseGeocoding,
  onPinMove,
  onConfirm,
  onClose,
}) {
  return (
    <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4">
      <div className="relative flex h-[80vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Drag the pin to your exact location</h3>
            {isReverseGeocoding && (
              <p className="text-xs text-gray-500 mt-1">Finding address...</p>
            )}
          </div>
          <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-900">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-grow w-full relative min-h-[320px]">
          {tempLocation.address && (
            <div className="absolute inset-x-4 bottom-4 z-10 rounded-lg border border-gray-200 bg-white/95 px-3 py-2 text-sm text-gray-700 shadow-sm">
              {tempLocation.address}
            </div>
          )}
          <MapPinPicker
            apiKey={apiKey}
            isLoaded={isMapLoaded}
            latitude={tempLocation.lat}
            longitude={tempLocation.lng}
            onPinMove={onPinMove}
          />
        </div>
        <div className="p-4 border-t bg-white flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 transition"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!Number.isFinite(tempLocation.lat) || !Number.isFinite(tempLocation.lng)}
            onClick={onConfirm}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-white font-semibold hover:bg-indigo-700 transition disabled:cursor-not-allowed disabled:opacity-40"
          >
            Confirm Location
          </button>
        </div>
      </div>
    </div>
  );
}
