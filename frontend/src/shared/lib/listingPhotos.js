export function listingPhotos(listing) {
  const raw = [
    ...(Array.isArray(listing?.images) ? listing.images : []),
    ...(Array.isArray(listing?.photos) ? listing.photos : []),
  ].filter(Boolean);
  const gallery = Array.from(new Set(raw));

  let grid = listing?.photos?.filter(Boolean) || [];
  if (grid.length >= 5) {
    grid = grid.slice(0, 5);
  } else if (grid.length === 0) {
    grid = Array.from({ length: 5 }).map(() => null);
  } else {
    const repeated = [...grid];
    while (repeated.length < 5) {
      repeated.push(grid[repeated.length % grid.length]);
    }
    grid = repeated.slice(0, 5);
  }

  return { grid, gallery };
}
