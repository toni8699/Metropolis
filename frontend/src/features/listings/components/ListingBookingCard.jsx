import { useCallback, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";
import PricingBreakdown from "@/shared/components/PricingBreakdown";
import { useClickOutside } from "@/shared/hooks/useClickOutside";
import {
  airbnbDayPickerClassNames,
  bookedDayModifierClassNames,
  defaultDateRangeFromToday,
  sanitizeDateRange,
  startOfToday,
} from "@/shared/lib/datePicker";
import { dateRangeOverlapsBooked } from "@/shared/lib/bookingDates";

export default function ListingBookingCard({
  pricePerDay,
  dateRange,
  onDateRangeChange,
  bookedRanges,
  calendarDisabledMatchers,
  calendarBookedModifiers,
  calendarMonths,
  onReserve,
  reserveButtonDisabled,
  reserveError,
  pricing,
  hasCompleteRange,
}) {
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  const calendarRef = useRef(null);
  const closeCalendar = useCallback(() => setIsCalendarOpen(false), []);

  useClickOutside(calendarRef, closeCalendar, isCalendarOpen);

  return (
    <div className="sticky top-6 rounded-[2rem] border-4 border-black bg-vroom-surface p-6 shadow-neo">
      <div className="flex items-baseline gap-1">
        <p className="text-3xl font-extrabold text-black">${pricePerDay}</p>
        <p className="font-semibold text-vroom-muted">/ day</p>
      </div>

      <div ref={calendarRef} className="relative mt-6">
        <div
          className="relative flex cursor-pointer rounded-2xl border-4 border-black bg-white"
          onClick={() => setIsCalendarOpen((open) => !open)}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              setIsCalendarOpen((open) => !open);
            }
          }}
        >
          <div className="w-1/2 p-3">
            <p className="text-[10px] font-bold text-gray-800">CHECK-IN</p>
            <p className="text-sm text-gray-500">
              {dateRange.from ? format(dateRange.from, "MM/dd/yyyy") : "Add date"}
            </p>
          </div>
          <div className="w-1/2 border-l-2 border-black p-3">
            <p className="text-[10px] font-bold text-gray-800">CHECKOUT</p>
            <p className="text-sm text-gray-500">
              {dateRange.to ? format(dateRange.to, "MM/dd/yyyy") : "Add date"}
            </p>
          </div>
        </div>

        {isCalendarOpen && (
          <div className="absolute right-0 top-[100%] z-50 mt-4 rounded-3xl border-4 border-black bg-vroom-surface p-6 shadow-neoBlack">
            <DayPicker
              mode="range"
              numberOfMonths={calendarMonths}
              startMonth={startOfToday()}
              disabled={calendarDisabledMatchers}
              modifiers={calendarBookedModifiers}
              modifiersClassNames={bookedDayModifierClassNames}
              selected={dateRange}
              onSelect={(range) => {
                const next = sanitizeDateRange(range);
                if (dateRangeOverlapsBooked(next.from, next.to, bookedRanges)) {
                  return;
                }
                onDateRangeChange(next);
              }}
              className="rdp-airbnb"
              classNames={airbnbDayPickerClassNames(true)}
              components={{
                Chevron: ({ orientation, ...props }) =>
                  orientation === "left" ? (
                    <ChevronLeft {...props} className="h-5 w-5" />
                  ) : (
                    <ChevronRight {...props} className="h-5 w-5" />
                  ),
              }}
            />
            <div className="mt-4 flex items-center justify-between border-t-4 border-black pt-4">
              <button
                type="button"
                onClick={() => onDateRangeChange(defaultDateRangeFromToday())}
                className="cursor-pointer text-sm font-medium text-gray-600 underline hover:text-black"
              >
                Clear dates
              </button>
              <button
                type="button"
                onClick={closeCalendar}
                className="rounded-full border-4 border-black border-b-4 border-r-4 bg-vroom-text px-4 py-2 text-sm font-bold text-white active:translate-x-1 active:translate-y-1 active:border-0"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={onReserve}
        disabled={reserveButtonDisabled}
        className="neo-btn-primary mt-4 w-full py-3 font-black"
      >
        Reserve
      </button>
      <p className="mt-3 text-center text-sm text-gray-500">You won&apos;t be charged yet</p>
      {reserveError && <p className="neo-error mt-3">{reserveError}</p>}
      {hasCompleteRange && pricing ? (
        <div className="mt-5 border-t-4 border-black pt-4">
          <PricingBreakdown
            pricePerDay={pricePerDay}
            dayCount={pricing.dayCount}
            subtotal={pricing.subtotal}
            cleaningFee={pricing.cleaningFee}
            serviceFee={pricing.serviceFee}
            total={pricing.total}
            currencyLabel=""
            showNightsLabel
          />
        </div>
      ) : (
        <p className="mt-4 text-center text-sm text-gray-500">Add dates to see price</p>
      )}
    </div>
  );
}
