import { Search } from "lucide-react";

export default function CollapsedSearchPill({
  location,
  collapsedWhenLabel,
  onOpen,
}) {
  return (
    <button
      onClick={onOpen}
      className="mx-auto flex h-14 w-full max-w-lg cursor-pointer items-center rounded-full border border-gray-300 bg-white py-2 pl-3 pr-2 shadow-sm transition hover:shadow-md md:max-w-xl"
    >
      <div className="min-w-[120px] flex-1 px-2 text-center text-base font-bold text-gray-900 sm:min-w-[200px]">
        {location || "Anywhere"}
      </div>
      <div className="mx-1.5 h-4 w-[1px] flex-shrink-0 bg-gray-300" />
      <div className="min-w-[120px] flex-1 px-2 text-center text-sm text-gray-700 sm:min-w-[210px]">
        {collapsedWhenLabel}
      </div>
      <div className="ml-1.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white">
        <Search className="h-4.5 w-4.5" strokeWidth={3} />
      </div>
    </button>
  );
}
