/** Checkout fee breakdown (CAD) — shared by checkout UI and tests. */
export function computeCheckoutTotals(pricePerDay, dayCount) {
  const nights = Math.max(1, Number(dayCount) || 1);
  const rate = Number(pricePerDay) || 0;
  const subtotal = rate * nights;
  const cleaningFee = 50;
  const serviceFee = Number((subtotal * 0.1).toFixed(2));
  const total = Number((subtotal + cleaningFee + serviceFee).toFixed(2));
  return { subtotal, cleaningFee, serviceFee, total, dayCount: nights };
}
