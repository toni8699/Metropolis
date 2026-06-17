import { Calendar, Camera, FileText } from "lucide-react";
import BodyCard from "@/shared/components/BodyCard";
import {
  newestListing,
  shouldShowOptimizationChecklist,
} from "@/features/host/lib/recentListing";

const checklistItems = [
  {
    icon: Camera,
    title: "Add more photos",
    buildDescription: (photoCount) =>
      `You have ${photoCount} photos. Listings with 10+ photos get 2x more clicks.`,
  },
  {
    icon: FileText,
    title: "Refine your description",
    buildDescription: () =>
      "Tell guests about your car's unique features (e.g., Carplay, child seats).",
  },
  {
    icon: Calendar,
    title: "Calendar Sync",
    buildDescription: () => "Avoid cancellations by syncing your personal calendar.",
  },
];

export default function OptimizationChecklist({ listings = [], isAdmin = false }) {
  if (!shouldShowOptimizationChecklist(listings, { isAdmin })) {
    return null;
  }

  const focusListing = newestListing(listings);
  const photoCount = Array.isArray(focusListing?.images)
    ? focusListing.images.filter(Boolean).length
    : 0;

  return (
    <section className="px-11 pt-11">
      <BodyCard className="bg-[#dbe8be] rounded-2xl p-6 sm:p-8">
        <h2 className="font-['Fredoka'] text-2xl font-extrabold text-[#183B1E]">
          Boost your listing
        </h2>
        <p className="mt-1 text-sm font-medium text-[#35593b]">
          Quick wins while your car is fresh on the marketplace.
        </p>
        <ul className="mt-6 space-y-4">
          {checklistItems.map((item) => {
            const Icon = item.icon;
            return (
              <li
                key={item.title}
                className="flex gap-4 rounded-xl border-2 border-black bg-[#FCFCE5] p-4"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-black bg-white">
                  <Icon className="h-5 w-5 text-[#E34B31]" aria-hidden />
                </div>
                <div>
                  <p className="font-bold text-[#183B1E]">{item.title}</p>
                  <p className="mt-1 text-sm text-[#35593b]">
                    {item.buildDescription(photoCount)}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      </BodyCard>
    </section>
  );
}
