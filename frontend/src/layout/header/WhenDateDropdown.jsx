import { ChevronLeft, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";
import {
  airbnbDayPickerClassNames,
  disabledBeforeTodayMatcher,
  sanitizeDateRange,
  startOfToday,
} from "@/shared/lib/datePicker";

export default function WhenDateDropdown({
  todayDate,
  tomorrowDate,
  previewNextSaturday,
  previewNextSunday,
  setToday,
  setTomorrow,
  setNextWeekend,
  selectedRange,
  setSelectedRange,
}) {
  return (
    <div className="absolute top-[56px] left-1/2 z-50 flex w-[500px] -translate-x-1/2 gap-3 rounded-2xl border border-gray-200 bg-white p-3 shadow-xl">
      <div className="flex w-1/3 flex-col gap-2">
        <button
          onClick={setToday}
          className="cursor-pointer rounded-lg border border-gray-200 p-2.5 text-left transition hover:border-gray-900"
        >
          <p className="text-sm font-semibold text-gray-900">Today</p>
          <p className="text-sm text-gray-500">{format(todayDate, "EEE, MMM d")}</p>
        </button>
        <button
          onClick={setTomorrow}
          className="cursor-pointer rounded-lg border border-gray-200 p-2.5 text-left transition hover:border-gray-900"
        >
          <p className="text-sm font-semibold text-gray-900">Tomorrow</p>
          <p className="text-sm text-gray-500">
            {format(tomorrowDate, "EEE, MMM d")}
          </p>
        </button>
        <button
          onClick={setNextWeekend}
          className="cursor-pointer rounded-lg border border-gray-200 p-2.5 text-left transition hover:border-gray-900"
        >
          <p className="text-sm font-semibold text-gray-900">Next weekend</p>
          <p className="text-sm text-gray-500">
            {format(previewNextSaturday, "MMM d")} -{" "}
            {format(previewNextSunday, "MMM d")}
          </p>
        </button>
      </div>

      <div className="w-2/3">
        <DayPicker
          mode="range"
          numberOfMonths={2}
          startMonth={startOfToday()}
          disabled={disabledBeforeTodayMatcher()}
          selected={selectedRange}
          onSelect={(range) => setSelectedRange(sanitizeDateRange(range))}
          className="rdp-airbnb"
          classNames={airbnbDayPickerClassNames()}
          components={{
            Chevron: ({ orientation, ...props }) =>
              orientation === "left" ? (
                <ChevronLeft {...props} className="h-4 w-4" />
              ) : (
                <ChevronRight {...props} className="h-4 w-4" />
              ),
          }}
        />
      </div>
    </div>
  );
}
