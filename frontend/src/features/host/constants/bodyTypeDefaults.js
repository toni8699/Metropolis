/** Mirrors backend BODY_TYPE_DEFAULTS for client-side body-type re-guess. */
export {
  FUEL_TYPE_OPTIONS,
  TRANSMISSION_OPTIONS,
} from "@/shared/constants/vehicleSpecOptions";

export const BODY_TYPE_DEFAULTS = {
  SUV: { seats: 5, doors: 5, transmission: "AUTOMATIC" },
  MINIVAN: { seats: 7, doors: 5, transmission: "AUTOMATIC" },
  COUPE: { seats: 4, doors: 2, transmission: "AUTOMATIC" },
  SEDAN: { seats: 5, doors: 4, transmission: "AUTOMATIC" },
  TRUCK: { seats: 5, doors: 4, transmission: "AUTOMATIC" },
  WAGON: { seats: 5, doors: 4, transmission: "AUTOMATIC" },
  EV: { seats: 5, doors: 4, transmission: "AUTOMATIC" },
  OTHER: { seats: 5, doors: 4, transmission: "AUTOMATIC" },
};

export const REQUIRED_SPEC_FIELDS = ["seats", "fuelType", "transmission"];
