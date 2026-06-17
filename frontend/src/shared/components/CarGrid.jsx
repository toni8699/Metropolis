import CarCard from "@/shared/components/CarCard";

export default function CarGrid({ cars = [], distanceById = null, compact = false }) {
  const gridClass = compact
    ? "grid grid-cols-1 gap-x-8 gap-y-10 sm:grid-cols-2"
    : "grid grid-cols-1 gap-x-8 gap-y-12 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6";

  return (
    <div className={gridClass}>
      {cars.map((car) => (
        <CarCard
          key={car.id}
          car={car}
          distanceKm={distanceById?.[car.id] ?? car.distanceKm ?? null}
        />
      ))}
    </div>
  );
}
