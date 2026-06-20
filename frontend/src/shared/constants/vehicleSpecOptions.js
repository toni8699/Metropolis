export const TRANSMISSION_OPTIONS = [
  { value: "AUTOMATIC", label: "Automatic" },
  { value: "MANUAL", label: "Manual" },
];

export const FILTER_TRANSMISSION_OPTIONS = [
  { value: null, label: "Any" },
  ...TRANSMISSION_OPTIONS,
];

export const FUEL_TYPE_OPTIONS = [
  { value: "Gasoline", label: "Gasoline" },
  { value: "Electric", label: "Electric" },
  { value: "Hybrid", label: "Hybrid" },
  { value: "Diesel", label: "Diesel" },
];

export const SEAT_OPTIONS = [2, 4, 5, 7];
