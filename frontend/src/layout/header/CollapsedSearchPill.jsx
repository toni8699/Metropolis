import { Search } from "lucide-react";

export default function CollapsedSearchPill({
  location,
  collapsedWhenLabel,
  onOpen,
}) {
  return (
    <button
      onClick={onOpen}
      className="mx-auto flex h-16 w-full max-w-xl cursor-pointer items-center gap-2 rounded-full border-4 border-black bg-white px-4 py-3 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)] transition hover:translate-y-[-1px] md:max-w-2xl"
    >
      <div className="min-w-[120px] flex-1 px-2 text-center text-base font-extrabold text-[#2D5A27] sm:min-w-[200px]">
        {location || "Anywhere"}
      </div>
      <div className="mx-1.5 h-8 w-[2px] flex-shrink-0 bg-black" />
      <div className="min-w-[120px] flex-1 px-2 text-center text-sm font-medium text-[#35593b] sm:min-w-[210px]">
        {collapsedWhenLabel}
      </div>
      <div className="ml-1.5 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border-2 border-black bg-[#E34B31] text-white transition hover:scale-110">
        <Search className="h-4 w-4" strokeWidth={3} />
      </div>
    </button>
  );
}
