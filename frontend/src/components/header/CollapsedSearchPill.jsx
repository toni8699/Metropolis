import { Search } from "lucide-react";

export default function CollapsedSearchPill({
  location,
  collapsedWhenLabel,
  onOpen,
}) {
  return (
    <button
      onClick={onOpen}
      className="mx-auto flex h-20 w-full max-w-xl cursor-pointer items-center rounded-full border border-gray-300 bg-white py-3 pl-6 pr-3 shadow-sm transition hover:shadow-md md:max-w-2xl"
    >
      <div className="min-w-[150px] flex-1 px-3 text-center text-xl font-bold text-gray-900 sm:min-w-[260px]">
        {location || "Anywhere"}
      </div>
      <div className="mx-2 h-6 w-[1px] flex-shrink-0 bg-gray-300" />
      <div className="min-w-[150px] flex-1 px-3 text-center text-lg text-gray-700 sm:min-w-[280px]">
        {collapsedWhenLabel}
      </div>
      <div className="ml-2 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white">
        <Search className="h-6 w-6" strokeWidth={3} />
      </div>
    </button>
  );
}
