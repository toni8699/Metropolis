import { addDays, isBefore, parseISO, startOfDay } from "date-fns";

/** Local midnight today — use for min selectable date. */
export function startOfToday() {
  return startOfDay(new Date());
}

/** Default search / booking range: check-in today, checkout tomorrow. */
export function defaultDateRangeFromToday() {
  const from = startOfToday();
  return { from, to: addDays(from, 1) };
}

/** react-day-picker matcher: block past calendar days. */
export function disabledBeforeTodayMatcher() {
  return { before: startOfToday() };
}

/** Inclusive calendar-day interval for nights already booked (checkout day stays selectable). */
export function bookedRangeToDisabledInterval(range) {
  if (!range?.startAt || !range?.endAt) {
    return null;
  }
  const from = startOfDay(parseISO(String(range.startAt).slice(0, 10)));
  const checkoutDay = startOfDay(parseISO(String(range.endAt).slice(0, 10)));
  const to = addDays(checkoutDay, -1);
  if (isBefore(to, from)) {
    return { from, to: from };
  }
  return { from, to };
}

export function buildBookedDisabledMatchers(bookedRanges) {
  return (bookedRanges || [])
    .map(bookedRangeToDisabledInterval)
    .filter(Boolean);
}

export function buildListingDatePickerDisabled(bookedRanges) {
  return [disabledBeforeTodayMatcher(), ...buildBookedDisabledMatchers(bookedRanges)];
}

function dayInInclusiveInterval(day, from, to) {
  return !isBefore(day, from) && !isBefore(to, day);
}

/** Booked styling only for today onward (past nights stay plain disabled/grey). */
export function buildBookedModifiers(bookedRanges) {
  const intervals = buildBookedDisabledMatchers(bookedRanges);
  if (!intervals.length) {
    return {};
  }
  const today = startOfToday();
  return {
    booked: (date) => {
      const day = startOfDay(date);
      if (isBefore(day, today)) {
        return false;
      }
      return intervals.some(({ from, to }) => dayInInclusiveInterval(day, from, to));
    },
  };
}

export function buildHostBlockedModifiers(blockedRanges) {
  const intervals = buildBookedDisabledMatchers(blockedRanges);
  if (!intervals.length) {
    return {};
  }
  const today = startOfToday();
  return {
    hostBlocked: (date) => {
      const day = startOfDay(date);
      if (isBefore(day, today)) {
        return false;
      }
      return intervals.some(({ from, to }) => dayInInclusiveInterval(day, from, to));
    },
  };
}

export const bookedDayModifierClassNames = {
  booked: "rdp-booked",
};

export const hostBlockedDayModifierClassNames = {
  hostBlocked: "rdp-host-blocked",
};

export function sanitizeDateRange(range) {
  if (!range?.from) {
    return { from: undefined, to: undefined };
  }

  const today = startOfToday();
  let from = startOfDay(range.from);
  let to = range.to ? startOfDay(range.to) : undefined;

  if (isBefore(from, today)) {
    from = today;
  }
  if (to && isBefore(to, today)) {
    to = undefined;
  }
  if (to && !isBefore(from, to)) {
    to = undefined;
  }

  return { from, to };
}

export function airbnbDayPickerClassNames(compact = false) {
  const size = compact ? "h-10 w-10 md:h-12 md:w-12" : "h-12 w-12";
  const textSize = compact ? "text-sm" : "";

  return {
    month_caption: "pb-4 text-center text-lg font-semibold",
    weekdays: "mb-3",
    weekday: "text-xs font-medium text-gray-400 uppercase tracking-wide",
    day: `rdp-day ${size} p-0`,
    day_button: `rdp-day_button ${size} rounded-full flex items-center justify-center font-medium ${textSize} border border-transparent hover:border-gray-900`,
    selected: "rdp-selected font-semibold",
    range_start: "rdp-range_start",
    range_end: "rdp-range_end",
    range_middle: "rdp-range_middle",
    disabled: "[&>button]:text-gray-300 [&>button]:opacity-40 [&>button]:cursor-not-allowed [&>button]:hover:border-transparent",
    outside: "text-gray-300 opacity-50",
  };
}
