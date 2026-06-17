import { CarFront, ChevronLeft } from "lucide-react";
import { useEffect } from "react";

export default function ListingPhotoGrid({
  title,
  gridImages,
  galleryImages,
  isGalleryOpen,
  onOpenGallery,
  onCloseGallery,
}) {
  useEffect(() => {
    if (!isGalleryOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isGalleryOpen]);

  return (
    <>
      <div className="group relative mt-6 grid aspect-[2/1] grid-cols-1 gap-2 overflow-hidden rounded-[2rem] border-4 border-black md:aspect-[2.1] md:grid-cols-4">
        {[0, 1, 2, 3, 4].map((index) => (
          <div
            key={index}
            className={`overflow-hidden ${
              index === 0
                ? "h-full w-full md:col-span-2 md:row-span-2"
                : "hidden h-full w-full md:block"
            }`}
          >
            {gridImages[index] ? (
              <img
                src={gridImages[index]}
                alt={`${title} photo ${index + 1}`}
                className="h-full w-full cursor-pointer object-cover transition hover:opacity-90"
                onClick={onOpenGallery}
              />
            ) : (
              <div className="h-full w-full bg-gray-200" />
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={onOpenGallery}
          className="neo-btn-secondary absolute bottom-4 right-4 flex items-center gap-2 px-4 py-2 text-sm shadow-neoBlack"
        >
          <CarFront className="h-4 w-4" />
          Show all photos
        </button>
      </div>

      {isGalleryOpen && (
        <div className="fixed inset-0 z-[100] overflow-y-auto bg-vroom-surface">
          <div className="sticky top-0 z-10 flex items-center border-b-4 border-black bg-vroom-surface px-6 py-4">
            <button
              type="button"
              onClick={onCloseGallery}
              className="flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium hover:bg-vroom-sage"
            >
              <ChevronLeft className="h-4 w-4" />
              Back to listing
            </button>
          </div>
          <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-10">
            {galleryImages.length ? (
              galleryImages.map((imageUrl, idx) => (
                <img
                  key={`${imageUrl}-${idx}`}
                  src={imageUrl}
                  alt={`${title} gallery ${idx + 1}`}
                  className="h-auto w-full rounded-xl object-cover"
                />
              ))
            ) : (
              <div className="flex h-80 w-full items-center justify-center rounded-xl bg-gray-200 text-gray-500">
                No photos available.
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
