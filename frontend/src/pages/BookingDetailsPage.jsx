import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiPost } from "../lib/api";

export default function BookingDetailsPage() {
  const { bookingId } = useParams();
  const [booking, setBooking] = useState(null);
  const [instruction, setInstruction] = useState("");

  const load = () => apiGet(`/api/bookings/${bookingId}`, true).then((d) => setBooking(d.booking));

  useEffect(() => {
    load();
  }, [bookingId]);

  const sendInstruction = async () => {
    await apiPost(`/api/bookings/${bookingId}/instructions`, { message: instruction }, true);
    setInstruction("");
    load();
  };

  const pickup = async () => {
    await apiPost(`/api/bookings/${bookingId}/confirm-pickup`, {}, true);
    load();
  };

  const complete = async () => {
    await apiPost(`/api/bookings/${bookingId}/complete`, {}, true);
    load();
  };

  if (!booking) {
    return <p>Loading booking...</p>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Booking #{booking.bookingId}</h1>
      <p>Status: {booking.status}</p>
      <p>Listing: {booking.listingTitle}</p>

      <div className="space-y-2 rounded border border-slate-700 p-3">
        <p className="font-medium">Owner pickup instructions</p>
        <textarea
          className="w-full rounded bg-slate-900 p-2"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="Example: Key in lockbox beside front door."
        />
        <button className="rounded bg-violet-600 px-3 py-2" onClick={sendInstruction}>
          Send instruction (owner)
        </button>
      </div>

      <div className="flex gap-2">
        <button className="rounded bg-amber-600 px-3 py-2" onClick={pickup}>
          Confirm pickup
        </button>
        <button className="rounded bg-emerald-700 px-3 py-2" onClick={complete}>
          Complete trip
        </button>
      </div>

      <div className="space-y-2">
        <p className="font-medium">Instruction timeline</p>
        {(booking.instructions || []).map((i) => (
          <div key={i.instructionId} className="rounded border border-slate-700 p-2 text-sm">
            <p>{i.message}</p>
            <p className="text-slate-500">{i.sentAt}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
