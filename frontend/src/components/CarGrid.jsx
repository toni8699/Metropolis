import CarCard from "./CarCard";
import { mockCars } from "../data/mockCars";

export default function CarGrid({ cars = mockCars, distanceById = null, compact = false }) {
  const gridClass = compact
    ? "grid grid-cols-1 sm:grid-cols-2 gap-6"
    : "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-6";

  return (
    <section className={gridClass}>
      {cars.map((car) => (
        <CarCard
          key={car.id}
          car={car}
          distanceKm={distanceById?.[car.id] ?? car.distanceKm ?? null}
        />
      ))}
    </section>
  );
}
