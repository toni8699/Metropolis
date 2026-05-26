export default function InstantBookToggle({ checked, onChange, disabled = false }) {
  return (
    <label
      className={`flex cursor-pointer items-start justify-between gap-4 rounded-xl border border-gray-200 p-4 transition ${
        disabled ? "cursor-not-allowed opacity-60" : "hover:border-gray-300"
      }`}
    >
      <div>
        <p className="text-sm font-semibold text-gray-900">Instant Book</p>
        <p className="mt-1 text-sm text-gray-600">
          {checked
            ? "Renters are confirmed immediately when they book."
            : "You approve each booking request before it is confirmed."}
        </p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 h-7 w-12 shrink-0 rounded-full transition ${
          checked ? "bg-gray-900" : "bg-gray-300"
        }`}
      >
        <span
          className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition ${
            checked ? "left-5" : "left-0.5"
          }`}
        />
      </button>
    </label>
  );
}
