import { Search } from "lucide-react";

export default function CollapsedSearchPill({
  location,
  collapsedWhenLabel,
  onOpen,
}) {
  return (
    <button
      onClick={onOpen}
      className="mx-auto grid h-16 w-full max-w-xl cursor-pointer grid-cols-[1fr_auto_1fr_auto] items-center gap-0 rounded-full border-4 border-black bg-white px-4 py-3 shadow-neo transition hover:translate-y-[-1px] md:max-w-2xl"
    >
      <span className="min-w-[120px] px-2 text-center text-base font-extrabold text-vroom-text sm:min-w-[200px]">
        {location || "Anywhere"}
      </span>
      <span className="mx-1.5 h-8 w-[2px] shrink-0 bg-black" aria-hidden="true" />
      <span className="min-w-[120px] px-2 text-center text-sm font-medium text-vroom-muted sm:min-w-[210px]">
        {collapsedWhenLabel}
      </span>
      <span className="ml-1.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-black bg-vroom-accent text-white transition hover:scale-110">
        <Search className="h-4 w-4" strokeWidth={3} />
      </span>
    </button>
  );
}
