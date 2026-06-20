/** Mirrors backend BODY_TYPE_DEFAULTS for client-side body-type re-guess. */
export const BODY_TYPE_DEFAULTS = {
  SUV: { seats: 5, doors: 5, transmission: "Automatic" },
  MINIVAN: { seats: 7, doors: 5, transmission: "Automatic" },
  COUPE: { seats: 4, doors: 2, transmission: "Automatic" },
  SEDAN: { seats: 5, doors: 4, transmission: "Automatic" },
  TRUCK: { seats: 5, doors: 4, transmission: "Automatic" },
  WAGON: { seats: 5, doors: 4, transmission: "Automatic" },
  EV: { seats: 5, doors: 4, transmission: "Automatic" },
  OTHER: { seats: 5, doors: 4, transmission: "Automatic" },
};

export const REQUIRED_SPEC_FIELDS = ["seats", "fuelType", "transmission"];

export const TRANSMISSION_OPTIONS = [
  { value: "Automatic", label: "Automatic" },
  { value: "Manual", label: "Manual" },
];

export const FUEL_TYPE_OPTIONS = [
  { value: "Gas", label: "Gas" },
  { value: "Electric", label: "Electric" },
  { value: "Hybrid", label: "Hybrid" },
  { value: "Diesel", label: "Diesel" },
];
