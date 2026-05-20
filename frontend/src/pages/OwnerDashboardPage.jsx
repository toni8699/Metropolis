import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../utils/api";
import { useAuth } from "../context/AuthContext";

const initialForm = {
  title: "",
  brand: "",
  make: "",
  model: "",
  year: "",
  pricePerDay: 50,
  lat: 45.5017,
  lng: -73.5673,
  cityZone: "montreal-core",
};

export default function OwnerDashboardPage() {
  const { refreshMe } = useAuth();
  const [listings, setListings] = useState([]);
  const [form, setForm] = useState(initialForm);

  const loadListings = () =>
    apiGet("/api/owner/listings", true).then((data) => setListings(data.listings || []));

  useEffect(() => {
    loadListings();
  }, []);

  const createListing = async (e) => {
    e.preventDefault();
    await apiPost("/api/owner/listings", form, true);
    await refreshMe();
    setForm(initialForm);
    loadListings();
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Owner Dashboard</h1>

      <form className="grid gap-3 rounded-lg border border-slate-700 p-4" onSubmit={createListing}>
        <input
          className="rounded bg-slate-900 p-2"
          placeholder="Listing title"
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
        />
        <div className="grid gap-2 sm:grid-cols-4">
          <input
            className="rounded bg-slate-900 p-2"
            placeholder="Brand"
            value={form.brand}
            onChange={(e) => setForm((f) => ({ ...f, brand: e.target.value }))}
          />
          <input
            className="rounded bg-slate-900 p-2"
            placeholder="Make"
            value={form.make}
            onChange={(e) => setForm((f) => ({ ...f, make: e.target.value }))}
          />
          <input
            className="rounded bg-slate-900 p-2"
            placeholder="Model"
            value={form.model}
            onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
          />
          <input
            className="rounded bg-slate-900 p-2"
            type="number"
            placeholder="Year"
            value={form.year}
            onChange={(e) => setForm((f) => ({ ...f, year: e.target.value }))}
          />
        </div>
        <input
          className="rounded bg-slate-900 p-2"
          type="number"
          placeholder="Price per day"
          value={form.pricePerDay}
          onChange={(e) => setForm((f) => ({ ...f, pricePerDay: Number(e.target.value) }))}
        />
        <button className="rounded bg-emerald-600 px-4 py-2 font-medium hover:bg-emerald-500">
          Add listing
        </button>
      </form>

      <div className="space-y-2">
        {listings.map((l) => (
          <div key={l.listingId} className="rounded border border-slate-700 p-3">
            <p className="font-medium">
              {l.brand || ""} {l.make || ""} {l.model || l.title} {l.year || ""}
            </p>
            <p className="text-sm text-slate-400">${l.pricePerDay}/day</p>
          </div>
        ))}
      </div>
    </div>
  );
}
