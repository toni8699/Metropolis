import { Link } from "react-router-dom";

export default function TripsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-4 rounded-2xl border border-gray-200 bg-white p-8">
      <h1 className="text-3xl font-semibold text-gray-900">Trip requested</h1>
      <p className="text-gray-600">
        Your booking request was sent successfully. You can track status from your
        upcoming trips.
      </p>
      <div className="flex gap-3">
        <Link
          to="/"
          className="rounded-lg bg-indigo-600 px-5 py-2.5 font-medium text-white hover:bg-indigo-700"
        >
          Back to search
        </Link>
        <Link
          to="/host/dashboard"
          className="rounded-lg border border-gray-300 px-5 py-2.5 font-medium text-gray-700 hover:bg-gray-50"
        >
          Host Dashboard
        </Link>
      </div>
    </div>
  );
}
