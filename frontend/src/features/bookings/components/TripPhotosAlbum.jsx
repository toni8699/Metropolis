import { useEffect, useMemo, useState } from "react";
import { ChevronRight, FolderOpen, Loader2, Plus, X } from "lucide-react";

const PREVIEW_LIMIT = 4;

export default function TripPhotosAlbum({
  photos,
  queueJobs = [],
  canUpload,
  busyKey,
  onAddPhoto,
  onDelete,
  onRetry,
}) {
  const [viewerOpen, setViewerOpen] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState(null);

  const queueItems = queueJobs.filter(
    (job) =>
      job.localPreviewUrl &&
      (job.status === "queued" || job.status === "uploading" || job.status === "failed"),
  );

  const items = useMemo(
    () => [
      ...photos.map((photo) => ({
        id: `photo-${photo.photoId}`,
        src: photo.fileUrl,
        label: photo.label,
        photo,
        uploading: false,
        failed: false,
        canDelete: true,
      })),
      ...queueItems.map((job) => ({
        id: job.id,
        src: job.localPreviewUrl,
        label: job.label || "Uploading",
        photo: null,
        uploading: job.status === "queued" || job.status === "uploading",
        failed: job.status === "failed",
        jobId: job.id,
        canDelete: false,
      })),
    ],
    [photos, queueItems],
  );

  const total = items.length;
  const previewItems = items.slice(0, PREVIEW_LIMIT);
  const overflow = Math.max(0, total - PREVIEW_LIMIT);

  useEffect(() => {
    if (!viewerOpen) return undefined;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [viewerOpen]);

  useEffect(() => {
    if (lightboxIndex == null) return undefined;
    const onEsc = (event) => {
      if (event.key === "Escape") setLightboxIndex(null);
    };
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, [lightboxIndex]);

  const openViewer = () => {
    if (total > 0 || canUpload) setViewerOpen(true);
  };

  const openLightbox = (index) => {
    if (!items[index]?.uploading && !items[index]?.failed) {
      setLightboxIndex(index);
    }
  };

  return (
    <>
      <div className="rounded-2xl border-2 border-black bg-vroom-surface shadow-neoSm">
        <button
          type="button"
          onClick={openViewer}
          disabled={total === 0 && !canUpload}
          className="flex w-full items-center gap-2 border-b-2 border-black px-4 py-3 text-left transition hover:bg-vroom-sage/30 disabled:cursor-default disabled:hover:bg-transparent"
        >
          <FolderOpen className="h-5 w-5 shrink-0 text-vroom-heading" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-extrabold text-vroom-heading">Trip photos</p>
            <p className="text-xs text-gray-600">
              {total === 0
                ? canUpload
                  ? "Tap to open album and add photos"
                  : "No photos yet"
                : `${total} photo${total === 1 ? "" : "s"} · Tap to open album`}
            </p>
          </div>
          {(total > 0 || canUpload) && (
            <ChevronRight className="h-5 w-5 shrink-0 text-vroom-heading" aria-hidden />
          )}
        </button>

        <div className="p-3">
          {total === 0 && !canUpload ? (
            <p className="py-4 text-center text-xs text-gray-500">Album empty.</p>
          ) : (
            <button
              type="button"
              onClick={openViewer}
              className="grid w-full grid-cols-4 gap-2 text-left"
            >
              {previewItems.map((item, index) => (
                <PreviewThumb
                  key={item.id}
                  item={item}
                  overflow={index === PREVIEW_LIMIT - 1 ? overflow : 0}
                />
              ))}
              {total === 0 && canUpload && (
                <div className="flex aspect-square flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-400 bg-white text-gray-500">
                  <Plus className="h-5 w-5" />
                  <span className="mt-1 text-[10px] font-bold">Add</span>
                </div>
              )}
            </button>
          )}
        </div>
      </div>

      {viewerOpen && (
        <AlbumViewer
          items={items}
          canUpload={canUpload}
          busyKey={busyKey}
          onClose={() => setViewerOpen(false)}
          onAddPhoto={() => {
            setViewerOpen(false);
            onAddPhoto?.();
          }}
          onOpenPhoto={openLightbox}
          onDelete={onDelete}
          onRetry={onRetry}
        />
      )}

      {lightboxIndex != null && items[lightboxIndex] && (
        <PhotoLightbox
          items={items}
          index={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
          onChange={setLightboxIndex}
        />
      )}
    </>
  );
}

function PreviewThumb({ item, overflow }) {
  return (
    <div className="relative aspect-square overflow-hidden rounded-xl border-2 border-black bg-white">
      <img src={item.src} alt={item.label} className="h-full w-full object-cover" />
      {item.uploading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
          <Loader2 className="h-5 w-5 animate-spin text-white" />
        </div>
      )}
      {overflow > 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/55 text-sm font-extrabold text-white">
          +{overflow}
        </div>
      )}
    </div>
  );
}

function AlbumViewer({
  items,
  canUpload,
  busyKey,
  onClose,
  onAddPhoto,
  onOpenPhoto,
  onDelete,
  onRetry,
}) {
  useEffect(() => {
    const onEsc = (event) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[135] flex flex-col bg-vroom-surface"
      role="dialog"
      aria-modal="true"
      aria-labelledby="trip-album-title"
    >
      <header className="flex shrink-0 items-center justify-between border-b-2 border-black px-4 py-3 shadow-neoSm">
        <div className="flex items-center gap-2">
          <FolderOpen className="h-5 w-5 text-vroom-heading" aria-hidden />
          <div>
            <h2 id="trip-album-title" className="text-lg font-extrabold text-vroom-heading">
              Trip photos
            </h2>
            <p className="text-xs text-gray-600">{items.length} in album</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full border-2 border-black bg-white p-2 hover:bg-vroom-sage"
          aria-label="Close album"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        {items.length === 0 ? (
          <p className="py-12 text-center text-sm text-gray-500">No photos yet.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {items.map((item, index) => (
              <AlbumThumb
                key={item.id}
                src={item.src}
                label={item.label}
                canUpload={canUpload && item.canDelete}
                busy={item.photo && busyKey === `delete-${item.photo.photoId}`}
                uploading={item.uploading}
                failed={item.failed}
                onOpen={() => onOpenPhoto(index)}
                onDelete={item.photo ? () => onDelete(item.photo) : undefined}
                onRetry={item.jobId ? () => onRetry?.(item.jobId) : undefined}
              />
            ))}
          </div>
        )}
      </div>

      {canUpload && (
        <footer className="shrink-0 border-t-2 border-black p-4">
          <button
            type="button"
            onClick={onAddPhoto}
            disabled={busyKey === "pick"}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full border-2 border-black bg-vroom-accent px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50"
          >
            {busyKey === "pick" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Add photo
          </button>
        </footer>
      )}
    </div>
  );
}

function AlbumThumb({
  src,
  label,
  canUpload,
  busy,
  uploading,
  failed,
  onOpen,
  onDelete,
  onRetry,
}) {
  return (
    <div className="group relative aspect-square overflow-hidden rounded-xl border-2 border-black bg-white">
      <button type="button" onClick={onOpen} className="block h-full w-full">
        <img src={src} alt={label} className="h-full w-full object-cover" />
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent px-2 pb-2 pt-8">
          <p className="truncate text-left text-xs font-semibold text-white">{label}</p>
        </div>
      </button>
      {uploading && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/40">
          <Loader2 className="h-6 w-6 animate-spin text-white" />
        </div>
      )}
      {failed && (
        <button
          type="button"
          onClick={onRetry}
          className="absolute inset-0 flex items-center justify-center bg-red-900/50 text-xs font-bold text-white"
        >
          Tap to retry
        </button>
      )}
      {canUpload && onDelete && !uploading && (
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onDelete();
          }}
          disabled={busy}
          className="absolute right-1.5 top-1.5 rounded-full border border-black bg-white/95 p-1 disabled:opacity-50"
          aria-label={`Delete ${label}`}
        >
          {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <X className="h-3.5 w-3.5" />}
        </button>
      )}
    </div>
  );
}

function PhotoLightbox({ items, index, onClose, onChange }) {
  const viewable = items.filter((item) => !item.uploading && !item.failed);
  const current = items[index];
  const viewIndex = viewable.findIndex((item) => item.id === current?.id);

  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, []);

  if (!current || viewIndex < 0) return null;

  const goPrev = () => {
    const next = (viewIndex - 1 + viewable.length) % viewable.length;
    const targetIndex = items.findIndex((item) => item.id === viewable[next].id);
    onChange(targetIndex);
  };

  const goNext = () => {
    const next = (viewIndex + 1) % viewable.length;
    const targetIndex = items.findIndex((item) => item.id === viewable[next].id);
    onChange(targetIndex);
  };

  return (
    <div
      className="fixed inset-0 z-[145] flex items-center justify-center bg-black/80 p-4"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div className="relative w-full max-w-3xl" onClick={(event) => event.stopPropagation()}>
        <button
          type="button"
          onClick={onClose}
          className="absolute -right-1 -top-1 z-10 rounded-full border-2 border-black bg-white p-1.5"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
        {viewable.length > 1 && (
          <>
            <button
              type="button"
              onClick={goPrev}
              className="absolute left-0 top-1/2 -translate-y-1/2 rounded-full border-2 border-black bg-white px-3 py-2 text-sm font-bold"
            >
              ‹
            </button>
            <button
              type="button"
              onClick={goNext}
              className="absolute right-0 top-1/2 -translate-y-1/2 rounded-full border-2 border-black bg-white px-3 py-2 text-sm font-bold"
            >
              ›
            </button>
          </>
        )}
        <img
          src={current.src}
          alt={current.label}
          className="max-h-[80vh] w-full rounded-xl border-2 border-black object-contain"
        />
        <p className="mt-3 text-center text-sm font-bold text-white">{current.label}</p>
        {viewable.length > 1 && (
          <p className="mt-1 text-center text-xs text-gray-300">
            {viewIndex + 1} of {viewable.length}
          </p>
        )}
      </div>
    </div>
  );
}
