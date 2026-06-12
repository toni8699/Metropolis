import CarCard from "@/shared/components/CarCard";

export default function CarGrid({ cars = [], distanceById = null, compact = false }) {
  const gridClass = compact
    ? "grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-8"
    : "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-x-6 gap-y-10";

  return (
    <section className={`mx-auto w-full max-w-screen-2xl px-4 py-8 md:px-6 lg:px-8 ${gridClass}`}>
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
