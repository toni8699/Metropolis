export default function PricingBreakdown({
  pricePerDay,
  dayCount,
  subtotal,
  cleaningFee,
  serviceFee,
  total,
  currencyLabel = "CAD",
  showNightsLabel = true,
}) {
  return (
    <div className="space-y-3 text-sm text-vroom-muted">
      <div className="flex items-center justify-between">
        <p className={showNightsLabel ? "underline" : ""}>
          ${Number(pricePerDay).toFixed(showNightsLabel ? 0 : 2)}
          {currencyLabel ? ` ${currencyLabel}` : ""} x {dayCount}{" "}
          {showNightsLabel ? "nights" : "days"}
        </p>
        <p>${subtotal.toFixed(2)}</p>
      </div>
      <div className="flex items-center justify-between">
        <p className={showNightsLabel ? "underline" : ""}>Cleaning fee</p>
        <p>${cleaningFee.toFixed(2)}</p>
      </div>
      <div className="flex items-center justify-between">
        <p className={showNightsLabel ? "underline" : ""}>
          {showNightsLabel ? "Service fee" : "VROOM service fee"}
        </p>
        <p>${serviceFee.toFixed(2)}</p>
      </div>
      <div className="flex items-center justify-between border-t-4 border-black pt-3 text-base font-semibold text-black">
        <p>{showNightsLabel ? "Total before taxes" : `Total (${currencyLabel})`}</p>
        <p>${total.toFixed(2)}</p>
      </div>
    </div>
  );
}
