import { ChevronLeft, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";

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
    <div className="absolute top-[80px] left-1/2 z-50 flex w-[700px] -translate-x-1/2 gap-8 rounded-[2rem] border border-gray-200 bg-white p-8 shadow-2xl">
      <div className="flex w-1/3 flex-col gap-4">
        <button
          onClick={setToday}
          className="cursor-pointer rounded-2xl border border-gray-200 p-4 text-left transition hover:border-gray-900"
        >
          <p className="text-sm font-semibold text-gray-900">Today</p>
          <p className="text-sm text-gray-500">{format(todayDate, "EEE, MMM d")}</p>
        </button>
        <button
          onClick={setTomorrow}
          className="cursor-pointer rounded-2xl border border-gray-200 p-4 text-left transition hover:border-gray-900"
        >
          <p className="text-sm font-semibold text-gray-900">Tomorrow</p>
          <p className="text-sm text-gray-500">
            {format(tomorrowDate, "EEE, MMM d")}
          </p>
        </button>
        <button
          onClick={setNextWeekend}
          className="cursor-pointer rounded-2xl border border-gray-200 p-4 text-left transition hover:border-gray-900"
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
          selected={selectedRange}
          onSelect={setSelectedRange}
          className="rdp-airbnb"
          classNames={{
            month_caption: "pb-4 text-center text-lg font-semibold",
            weekdays: "mb-3",
            weekday: "text-xs font-medium text-gray-400 uppercase tracking-wide",
            day: "h-12 w-12 p-0",
            day_button:
              "h-12 w-12 rounded-full flex items-center justify-center font-medium border border-transparent hover:border-gray-900",
            selected: "bg-gray-900 text-white rounded-full border-gray-900",
            range_start: "bg-gray-900 text-white rounded-full border-gray-900",
            range_end: "bg-gray-900 text-white rounded-full border-gray-900",
            range_middle: "bg-gray-100 text-gray-900 rounded-none border-transparent",
          }}
          components={{
            Chevron: ({ orientation, ...props }) =>
              orientation === "left" ? (
                <ChevronLeft {...props} className="h-5 w-5" />
              ) : (
                <ChevronRight {...props} className="h-5 w-5" />
              ),
          }}
        />
      </div>
    </div>
  );
}
