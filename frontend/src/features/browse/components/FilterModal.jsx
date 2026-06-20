import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { apiGet } from "@/shared/api/api";
import { featureIcon } from "@/shared/lib/featureIcon";
import {
  FILTER_TRANSMISSION_OPTIONS,
  FUEL_TYPE_OPTIONS,
  SEAT_OPTIONS,
} from "@/shared/constants/vehicleSpecOptions";
import { DEFAULT_FILTERS, PRICE_DOMAIN } from "@/features/browse/lib/filterParams";

function toggleInList(list, value) {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

function PriceRangeSlider({ minPrice, maxPrice, onChange }) {
  const lo = minPrice ?? PRICE_DOMAIN.min;
  const hi = maxPrice ?? PRICE_DOMAIN.max;

  const setLo = (value) => {
    const nextLo = Math.min(Number(value), hi);
    onChange({
      minPrice: nextLo <= PRICE_DOMAIN.min ? null : nextLo,
      maxPrice: maxPrice,
    });
  };

  const setHi = (value) => {
    const nextHi = Math.max(Number(value), lo);
    onChange({
      minPrice,
      maxPrice: nextHi >= PRICE_DOMAIN.max ? null : nextHi,
    });
  };

  const loPct = ((lo - PRICE_DOMAIN.min) / (PRICE_DOMAIN.max - PRICE_DOMAIN.min)) * 100;
  const hiPct = ((hi - PRICE_DOMAIN.min) / (PRICE_DOMAIN.max - PRICE_DOMAIN.min)) * 100;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm font-semibold text-vroom-text">
        <span>${lo}/day</span>
        <span>${hi}/day</span>
      </div>
      <div className="relative h-8">
        <div className="absolute top-1/2 h-2 w-full -translate-y-1/2 rounded-full bg-gray-200" />
        <div
          className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full bg-vroom-heading"
          style={{ left: `${loPct}%`, right: `${100 - hiPct}%` }}
        />
        <input
          type="range"
          min={PRICE_DOMAIN.min}
          max={PRICE_DOMAIN.max}
          value={lo}
          onChange={(event) => setLo(event.target.value)}
          className="pointer-events-none absolute inset-0 z-20 w-full appearance-none bg-transparent [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-black [&::-webkit-slider-thumb]:bg-vroom-gold"
        />
        <input
          type="range"
          min={PRICE_DOMAIN.min}
          max={PRICE_DOMAIN.max}
          value={hi}
          onChange={(event) => setHi(event.target.value)}
          className="pointer-events-none absolute inset-0 z-30 w-full appearance-none bg-transparent [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-black [&::-webkit-slider-thumb]:bg-vroom-coral"
        />
      </div>
    </div>
  );
}

export default function FilterModal({
  isOpen,
  onClose,
  draft,
  onChange,
  count,
  isCountLoading,
  onApply,
  onClearAll,
}) {
  const [bodyTypes, setBodyTypes] = useState([]);
  const [features, setFeatures] = useState([]);

  useEffect(() => {
    if (!isOpen) return undefined;
    let cancelled = false;
    Promise.all([apiGet("/api/body-types"), apiGet("/api/features")])
      .then(([bodyData, featureData]) => {
        if (cancelled) return;
        setBodyTypes(bodyData?.bodyTypes || []);
        setFeatures(featureData?.features || []);
      })
      .catch(() => {
        if (!cancelled) {
          setBodyTypes([]);
          setFeatures([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const onEsc = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, [isOpen, onClose]);

  const featuresByCategory = useMemo(() => {
    return features.reduce((acc, feature) => {
      const category = feature.category || "Features";
      if (!acc[category]) acc[category] = [];
      acc[category].push(feature);
      return acc;
    }, {});
  }, [features]);

  if (!isOpen) return null;

  const safeDraft = draft || DEFAULT_FILTERS;
  const resultCount = count ?? 0;
  const showCount = isCountLoading ? "..." : resultCount;

  return (
    <div
      className="modal-enter fixed inset-0 z-[70] flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="filter-modal-title"
        className="flex max-h-[92vh] w-full max-w-2xl flex-col overflow-hidden rounded-t-3xl border-2 border-black bg-vroom-surface shadow-neoCard sm:rounded-3xl"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b-2 border-black px-5 py-4">
          <h2 id="filter-modal-title" className="text-xl font-extrabold text-vroom-heading">
            Filters
          </h2>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClearAll}
              className="text-xs font-bold uppercase tracking-wide text-vroom-muted hover:text-vroom-heading"
            >
              Clear All
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border-2 border-black bg-white p-2 hover:scale-105"
              aria-label="Close filters"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="flex-1 space-y-8 overflow-y-auto px-5 py-5">
          <section className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
              Price per day
            </h3>
            <PriceRangeSlider
              minPrice={safeDraft.minPrice}
              maxPrice={safeDraft.maxPrice}
              onChange={(pricePatch) => onChange((prev) => ({ ...prev, ...pricePatch }))}
            />
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
              Vehicle types
            </h3>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {bodyTypes.map((bodyType) => {
                const active = safeDraft.bodyTypeIds.includes(bodyType.bodyTypeId);
                return (
                  <button
                    key={bodyType.bodyTypeId}
                    type="button"
                    onClick={() =>
                      onChange((prev) => ({
                        ...prev,
                        bodyTypeIds: toggleInList(prev.bodyTypeIds, bodyType.bodyTypeId),
                      }))
                    }
                    className={`rounded-xl border-2 px-3 py-2 text-sm font-bold transition ${
                      active
                        ? "border-black bg-vroom-heading text-white shadow-neoSm"
                        : "border-black bg-white text-vroom-text hover:bg-vroom-accent/20"
                    }`}
                  >
                    {bodyType.displayName}
                  </button>
                );
              })}
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
              Specs
            </h3>
            <div className="space-y-4">
              <div>
                <p className="mb-2 text-xs font-semibold text-vroom-muted">Transmission</p>
                <div className="flex flex-wrap gap-2">
                  {FILTER_TRANSMISSION_OPTIONS.map((option) => {
                    const active = safeDraft.transmission === option.value;
                    return (
                      <button
                        key={option.label}
                        type="button"
                        onClick={() =>
                          onChange((prev) => ({ ...prev, transmission: option.value }))
                        }
                        className={`rounded-full border-2 px-4 py-1.5 text-xs font-bold ${
                          active
                            ? "border-black bg-vroom-coral text-vroom-text"
                            : "border-black bg-white text-vroom-text"
                        }`}
                      >
                        {option.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <p className="mb-2 text-xs font-semibold text-vroom-muted">Seats</p>
                <div className="flex flex-wrap gap-2">
                  {SEAT_OPTIONS.map((seat) => {
                    const active = safeDraft.seats.includes(seat);
                    const label = seat === 7 ? "7+" : String(seat);
                    return (
                      <button
                        key={seat}
                        type="button"
                        onClick={() =>
                          onChange((prev) => ({
                            ...prev,
                            seats: toggleInList(prev.seats, seat),
                          }))
                        }
                        className={`rounded-full border-2 px-4 py-1.5 text-xs font-bold ${
                          active
                            ? "border-black bg-vroom-gold text-vroom-text"
                            : "border-black bg-white text-vroom-text"
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <p className="mb-2 text-xs font-semibold text-vroom-muted">Fuel type</p>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  {FUEL_TYPE_OPTIONS.map((option) => {
                    const active = safeDraft.fuelTypes.includes(option.value);
                    return (
                      <label
                        key={option.value}
                        className={`flex cursor-pointer items-center gap-2 rounded-xl border-2 px-3 py-2 text-sm font-semibold ${
                          active
                            ? "border-black bg-vroom-accent/30"
                            : "border-black bg-white"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={active}
                          onChange={() =>
                            onChange((prev) => ({
                              ...prev,
                              fuelTypes: toggleInList(prev.fuelTypes, option.value),
                            }))
                          }
                          className="h-4 w-4 accent-vroom-heading"
                        />
                        {option.label}
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
              Features
            </h3>
            {Object.entries(featuresByCategory).map(([category, categoryFeatures]) => (
              <div key={category} className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-vroom-muted">
                  {category}
                </p>
                <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                  {categoryFeatures.map((feature) => {
                    const Icon = featureIcon(feature.iconKey);
                    const active = safeDraft.featureIds.includes(feature.featureId);
                    return (
                      <label
                        key={feature.featureId}
                        className={`flex cursor-pointer items-center gap-2 rounded-xl border-2 px-3 py-2 text-sm font-semibold ${
                          active
                            ? "border-black bg-vroom-heading text-white"
                            : "border-black bg-white text-vroom-text"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={active}
                          onChange={() =>
                            onChange((prev) => ({
                              ...prev,
                              featureIds: toggleInList(prev.featureIds, feature.featureId),
                            }))
                          }
                          className="sr-only"
                        />
                        <Icon className="h-4 w-4 shrink-0" />
                        <span className="truncate">{feature.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </section>
        </div>

        <footer className="border-t-2 border-black bg-vroom-surface px-5 py-4">
          <button
            type="button"
            disabled={resultCount === 0 || isCountLoading}
            onClick={onApply}
            className="neo-btn-primary w-full py-3 text-sm font-extrabold disabled:cursor-not-allowed disabled:opacity-50"
          >
            {resultCount === 0 ? "0 Results" : `Show ${showCount} Results`}
          </button>
        </footer>
      </div>
    </div>
  );
}
