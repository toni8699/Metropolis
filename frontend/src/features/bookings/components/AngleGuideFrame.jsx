/**
 * Preview slot for one inspection angle.
 * ponytail: guideImageUrl hook for future custom art — pass URL when assets exist.
 */
export default function AngleGuideFrame({
  title,
  instruction,
  guideImageUrl = null,
  canUpload = false,
  busyKey,
  onPick,
  isSkipped = false,
  children,
}) {
  const picking = busyKey === "pick";

  const content = children || (
    <div className="flex flex-col items-center justify-center gap-2 px-4 text-center">
      {guideImageUrl ? (
        <img
          src={guideImageUrl}
          alt=""
          className="mb-2 max-h-28 w-full object-contain"
        />
      ) : null}
      {title ? (
        <p className="text-xs font-bold uppercase tracking-wide text-gray-500">Suggested</p>
      ) : null}
      {title ? (
        <p className="text-sm font-extrabold text-vroom-heading">{title}</p>
      ) : null}
      <p className="text-sm text-gray-700">{instruction}</p>
      {isSkipped ? (
        <p className="text-xs text-gray-500">Skipped — tap to add a photo</p>
      ) : canUpload ? (
        <p className="text-xs font-semibold text-vroom-accent">
          {picking ? "Opening picker…" : "Tap to add — camera or library"}
        </p>
      ) : (
        <p className="text-xs text-gray-500">No photo yet</p>
      )}
    </div>
  );

  const className =
    "relative flex min-h-[220px] w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-400 bg-gray-50 p-4 text-center transition";

  if (canUpload && onPick && !children) {
    return (
      <button
        type="button"
        onClick={onPick}
        disabled={picking}
        className={`${className} cursor-pointer hover:border-black hover:bg-vroom-sage/40 disabled:opacity-50`}
      >
        {content}
      </button>
    );
  }

  return <div className={className}>{content}</div>;
}
