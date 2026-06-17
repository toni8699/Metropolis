import { useMemo } from "react";
import {
  Bar,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import OptimizationChecklist from "@/features/host/components/OptimizationChecklist";
import { AnalyticsCard } from "@/features/host/components/form/Fields";
import {
  buildBookingsByLocation,
  buildRevenueSeries,
  formatBookingWindow,
} from "@/features/host/lib/dashboardAnalytics";

const pieColors = ["#4f46e5", "#818cf8", "#c7d2fe"];

export default function OverviewPanel({ analytics, bookings, listings = [], isAdmin }) {
  const recentBookings = useMemo(
    () =>
      bookings.slice(0, 5).map((booking) => ({
        user: booking.renterEmail || `User #${booking.renterUserId || "n/a"}`,
        car: booking.listingTitle || "Vehicle",
        dates: formatBookingWindow(booking.startAt, booking.endAt),
        status: booking.status || "PENDING",
      })),
    [bookings],
  );
  const revenueSeries = useMemo(() => buildRevenueSeries(bookings), [bookings]);
  const bookingsByLocationSeries = useMemo(
    () => buildBookingsByLocation(bookings),
    [bookings],
  );

  return (
    <>
      <OptimizationChecklist listings={listings} isAdmin={isAdmin} />

      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 p-11">
        <AnalyticsCard label="Total Listings" value={analytics?.listingCount ?? 0} />
        <AnalyticsCard label="Total Bookings" value={analytics?.bookingCount ?? 0} />
        <AnalyticsCard
          label="Gross Daily Revenue"
          value={`$${Number(analytics?.grossDailyRevenue || 0).toFixed(2)}`}
        />
        <AnalyticsCard
          label={isAdmin ? "Paid Revenue" : "Active Listings"}
          value={
            isAdmin
              ? `$${Number(analytics?.paidRevenue || 0).toFixed(2)}`
              : String(analytics?.activeListings ?? 0)
          }
        />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 px-11 mt-2">
        <div className="lg:col-span-2 rounded-2xl border-4 border-black bg-[#f5f5d0] p-6 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue (Past 30 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={revenueSeries}>
              <defs>
                <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="day" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#4f46e5"
                strokeWidth={3}
                dot={false}
              />
              <Bar dataKey="revenue" fill="url(#revenueFill)" opacity={0.25} barSize={16} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-2xl border-4 border-black bg-[#f5f5d0] p-6 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Bookings by Location</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={bookingsByLocationSeries}
                dataKey="bookings"
                nameKey="location"
                innerRadius={48}
                outerRadius={88}
                paddingAngle={3}
              >
                {bookingsByLocationSeries.map((entry, index) => (
                  <Cell key={entry.location} fill={pieColors[index % pieColors.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="mx-11 mt-6 overflow-hidden rounded-2xl border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Bookings</h3>
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold tracking-wider">
              <th className="px-6 py-4">User</th>
              <th className="px-6 py-4">Car</th>
              <th className="px-6 py-4">Dates</th>
              <th className="px-6 py-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {recentBookings.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-sm text-gray-500 text-center">
                  {isAdmin ? "No bookings yet." : "No bookings on your listings yet."}
                </td>
              </tr>
            ) : (
              recentBookings.map((row, idx) => (
                <tr
                  key={`${row.user}-${idx}`}
                  className="border-b border-gray-100 hover:bg-gray-50 transition"
                >
                  <td className="px-6 py-4 text-sm text-gray-900">{row.user}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{row.car}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{row.dates}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </>
  );
}
