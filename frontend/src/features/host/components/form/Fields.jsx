import { BarChart3, ChevronDown, DollarSign } from "lucide-react";

export function controlBorderClass(state = "default") {
  const base =
    "w-full border-2 rounded-2xl bg-white px-4 py-3 text-vroom-heading outline-none transition focus:ring-2 focus:ring-vroom-accent focus:ring-offset-1";
  if (state === "error") return `${base} border-red-500`;
  if (state === "estimate") return `${base} border-amber-500`;
  return `${base} border-black`;
}

export function FormFieldLabel({ children, badge = null }) {
  return (
    <div className="mb-2 flex items-center justify-between gap-2">
      <span className="text-sm font-bold text-vroom-muted">{children}</span>
      {badge}
    </div>
  );
}

export function NeoSelect({
  value,
  onChange,
  options,
  placeholder = "Select option",
  borderState = "default",
  required = false,
  disabled = false,
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        disabled={disabled}
        className={`${controlBorderClass(borderState)} appearance-none pr-10 disabled:bg-gray-100 disabled:text-gray-500`}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-vroom-muted"
        aria-hidden
      />
    </div>
  );
}

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

export function LabeledInput({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  required = false,
  disabled = false,
  borderState = "default",
}) {
  return (
    <label className="block">
      <FormFieldLabel>{label}</FormFieldLabel>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className={`${controlBorderClass(borderState)} disabled:bg-gray-100 disabled:text-gray-500`}
      />
    </label>
  );
}

export function LabeledTextarea({ label, value, onChange, placeholder }) {
  return (
    <label className="block">
      <FormFieldLabel>{label}</FormFieldLabel>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full min-h-28 border-2 border-black rounded-2xl bg-white px-4 py-3 text-vroom-heading outline-none transition resize-y focus:ring-2 focus:ring-vroom-accent focus:ring-offset-1"
      />
    </label>
  );
}

export function LabeledSelect({
  label,
  value,
  onChange,
  options,
  placeholder = "Select option",
  required = false,
  disabled = false,
  borderState = "default",
}) {
  return (
    <label className="block">
      <FormFieldLabel>{label}</FormFieldLabel>
      <NeoSelect
        value={value}
        onChange={onChange}
        options={options}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        borderState={borderState}
      />
    </label>
  );
}

export function LabeledPriceInput({ label, value, onChange }) {
  return (
    <label className="block">
      <FormFieldLabel>{label}</FormFieldLabel>
      <div className="relative">
        <DollarSign className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-vroom-accent" />
        <input
          type="number"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          required
          className="w-full border-2 border-black rounded-2xl bg-white py-3 pl-10 pr-4 text-vroom-heading outline-none transition focus:ring-2 focus:ring-vroom-accent focus:ring-offset-1"
        />
      </div>
    </label>
  );
}
