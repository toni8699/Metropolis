import {
  CarFront,
  Globe,
  Menu,
  Search,
  SlidersHorizontal,
  UserCircle2,
} from "lucide-react";
import { useState } from "react";

export default function Header({ onSearch }) {
  const [location, setLocation] = useState("montreal-core");
  const [pickupDate, setPickupDate] = useState("");
  const [returnDate, setReturnDate] = useState("");

  const handleSearch = () => {
    onSearch?.({
      location: location.trim(),
      pickupDate,
      returnDate,
    });
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50 w-full border-b bg-white">
      <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6 md:px-10 md:py-5 lg:px-12 xl:px-20">
        <div className="flex items-center gap-2 text-indigo-600">
          <CarFront className="h-7 w-7" />
          <span className="text-xl font-bold">DriveBnb</span>
        </div>

        <div className="hidden min-w-[400px] items-center overflow-hidden rounded-full border py-3 px-1 shadow-sm transition hover:shadow-md md:flex md:min-w-[450px]">
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Location"
            className="w-36 px-6 py-1 text-base font-medium outline-none"
          />
          <input
            value={pickupDate}
            onChange={(e) => setPickupDate(e.target.value)}
            type="date"
            className="border-l px-6 py-1 text-base font-medium outline-none"
          />
          <button
            onClick={onSearch}
            className="flex items-center gap-3 border-l py-1 pl-6 pr-2 text-base text-gray-500"
          >
            <input
              value={returnDate}
              onChange={(e) => setReturnDate(e.target.value)}
              type="date"
              className="w-36 bg-transparent outline-none"
            />
            <span
              role="button"
              onClick={handleSearch}
              className="cursor-pointer rounded-full bg-indigo-600 p-3 text-white"
            >
              <Search className="h-4 w-4" />
            </span>
          </button>
        </div>

        <div className="flex items-center gap-1">
          <button className="hidden cursor-pointer items-center gap-2 rounded-full border border-gray-300 px-4 py-2 text-sm font-medium transition hover:border-gray-900 md:flex">
            <SlidersHorizontal className="h-4 w-4" />
            Filters
          </button>
          <button className="rounded-full px-4 py-2 text-sm font-medium hover:bg-gray-100">
            Host your car
          </button>
          <button
            className="rounded-full p-2 hover:bg-gray-100"
            aria-label="Language selector"
          >
            <Globe className="h-5 w-5 text-gray-700" />
          </button>
          <button
            className="flex items-center gap-2 rounded-full border p-1 pl-3 transition hover:shadow-md"
            aria-label="User menu"
          >
            <Menu className="h-4 w-4 text-gray-700" />
            <UserCircle2 className="h-8 w-8 fill-gray-500 text-gray-500" />
          </button>
        </div>
      </div>
    </header>
  );
}
