import { describe, expect, it } from "vitest";
import { buildGroupedPhase, GROUP_ORDER } from "./tripInspectionGroups";

describe("buildGroupedPhase", () => {
  it("groups standard slots by API group field", () => {
    const phase = {
      slots: [
        {
          angleKey: "front_driver_corner",
          group: "exterior",
          title: "Front driver corner",
          instruction: "x",
          icon: "Camera",
          photo: { photoId: 1, fileUrl: "https://example.com/a.jpg" },
        },
        {
          angleKey: "dashboard",
          group: "interior",
          title: "Dashboard",
          instruction: "y",
          icon: "Gauge",
          photo: null,
        },
        {
          angleKey: "extra",
          isExtra: true,
          title: "Damage",
          photo: { photoId: 2, fileUrl: "https://example.com/b.jpg" },
        },
      ],
    };

    const { groups, extras } = buildGroupedPhase(phase);
    expect(GROUP_ORDER).toEqual(["exterior", "interior", "detail"]);
    expect(groups[0].slots).toHaveLength(1);
    expect(groups[0].slots[0].angleKey).toBe("front_driver_corner");
    expect(groups[1].slots[0].angleKey).toBe("dashboard");
    expect(groups[2].slots).toHaveLength(0);
    expect(extras).toHaveLength(1);
  });

  it("returns empty groups when API has no slots yet", () => {
    const { groups, extras } = buildGroupedPhase({ slots: [] });
    expect(groups.every((group) => group.slots.length === 0)).toBe(true);
    expect(extras).toHaveLength(0);
  });
});
