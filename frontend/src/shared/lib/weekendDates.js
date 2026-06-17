import { addDays } from "date-fns";
import { startOfToday } from "@/shared/lib/datePicker";

/** Next Sat–Sun from today (always future weekend, not this week if Sat passed). */
export function nextWeekendRange() {
  const today = startOfToday();
  const day = today.getDay();
  const daysUntilSaturday = (6 - day + 7) % 7 || 7;
  const saturday = addDays(today, daysUntilSaturday);
  const sunday = addDays(saturday, 1);
  return { saturday, sunday };
}
