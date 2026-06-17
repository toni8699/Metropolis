import { BarChart3, DollarSign } from "lucide-react";

export function AnalyticsCard({ label, value }) {
  return (
    <div className="bg-vroom-card border-4 border-black rounded-[1.5rem] p-6 shadow-neo flex flex-col gap-2">
      <p className="text-sm font-bold text-vroom-muted uppercase tracking-wider">{label}</p>
      <div className="flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-vroom-accent" />
        <p className="text-4xl font-extrabold text-vroom-heading">{value}</p>
      </div>
    </div>
  );
}

export function LabeledInput({ label, value, onChange, type = "text", placeholder, required = false }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-vroom-muted">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        className="w-full border-2 border-black rounded-2xl bg-white px-4 py-3 text-vroom-heading outline-none transition"
      />
    </label>
  );
}

export function LabeledTextarea({ label, value, onChange, placeholder }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-vroom-muted">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full min-h-28 border-2 border-black rounded-2xl bg-white px-4 py-3 text-vroom-heading outline-none transition resize-y"
      />
    </label>
  );
}

export function LabeledSelect({ label, value, onChange, options, required = false }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-vroom-muted">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        className="w-full border-2 border-black rounded-2xl bg-white px-4 py-3 text-vroom-heading outline-none transition"
      >
        <option value="">Select option</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function LabeledPriceInput({ label, value, onChange }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-vroom-muted">{label}</span>
      <div className="relative">
        <DollarSign className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-vroom-accent" />
        <input
          type="number"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          required
          className="w-full border-2 border-black rounded-2xl bg-white py-3 pl-10 pr-4 text-vroom-heading outline-none transition"
        />
      </div>
    </label>
  );
}
