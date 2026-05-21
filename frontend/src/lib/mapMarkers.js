/** Slight offset when many listings share one lat/lng (branch parking). */
export function spreadOverlappingMarkers(cars) {
  const buckets = new Map();

  for (const car of cars) {
    const key = `${car.lat.toFixed(5)}:${car.lng.toFixed(5)}`;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(car);
  }

  const spread = [];
  for (const group of buckets.values()) {
    if (group.length === 1) {
      spread.push(group[0]);
      continue;
    }

    group.forEach((car, index) => {
      if (index === 0) {
        spread.push(car);
        return;
      }
      const angle = (index / group.length) * Math.PI * 2;
      const meters = 18 + index * 6;
      const latRad = (car.lat * Math.PI) / 180;
      const dLat = (meters / 111111) * Math.cos(angle);
      const dLng = (meters / (111111 * Math.cos(latRad))) * Math.sin(angle);
      spread.push({
        ...car,
        lat: car.lat + dLat,
        lng: car.lng + dLng,
      });
    });
  }

  return spread;
}
