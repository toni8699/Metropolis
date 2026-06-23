import { GROUP_LABELS, GROUP_ORDER } from "@/features/bookings/lib/tripInspectionGroups";

export default function TripInspectionMilestoneBar({
  milestones,
  activeGroupKey,
  pulseGroupKey,
  onSelectGroup,
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-1">
        {milestones.map((milestone, index) => {
          const isActive = milestone.key === activeGroupKey;
          const isComplete = milestone.uploaded >= milestone.total && milestone.total > 0;
          const isPulsing = pulseGroupKey === milestone.key;

          return (
            <div key={milestone.key} className="flex flex-1 items-center">
              <button
                type="button"
                onClick={() => onSelectGroup?.(milestone.key)}
                className={`flex min-w-0 flex-1 flex-col items-center gap-0.5 rounded-xl border-2 px-1 py-1.5 text-center transition-transform ${
                  isActive
                    ? "border-black bg-vroom-sage shadow-neoSm"
                    : "border-gray-300 bg-white"
                } ${isPulsing ? "scale-105" : ""}`}
              >
                <span
                  className={`text-[10px] font-extrabold leading-tight ${
                    isActive || isComplete ? "text-vroom-heading" : "text-gray-500"
                  }`}
                >
                  {GROUP_LABELS[milestone.key] || milestone.key}
                </span>
                <span className="text-[10px] text-gray-600">
                  {milestone.uploaded}/{milestone.total}
                </span>
              </button>
              {index < milestones.length - 1 && (
                <div
                  className="mx-0.5 h-0.5 min-w-[8px] flex-1 rounded-full bg-gray-200"
                  aria-hidden
                >
                  <div
                    className="h-full rounded-full bg-vroom-accent transition-all duration-300"
                    style={{
                      width: isComplete ? "100%" : isActive ? "50%" : "0%",
                    }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-vroom-accent transition-all duration-300"
          style={{
            width: `${Math.min(
              100,
              (milestones.reduce((sum, m) => sum + m.uploaded, 0) /
                Math.max(1, milestones.reduce((sum, m) => sum + m.total, 0))) *
                100,
            )}%`,
          }}
        />
      </div>
    </div>
  );
}

export { GROUP_ORDER };
