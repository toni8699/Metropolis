import { describe, expect, it } from "vitest";
import {
  countRecommendedUploaded,
  countUploadedInGroup,
  findResumeStepIndex,
  flattenStandardSlots,
  getStepMeta,
  isLastStepInGroup,
} from "./tripInspectionLinearSteps";

const phase = {
  slots: [
    {
      angleKey: "front_driver_corner",
      group: "exterior",
      title: "Front driver corner",
      recommendedFirst: true,
      photo: { photoId: 1, fileUrl: "https://example.com/a.jpg" },
    },
    {
      angleKey: "front_passenger_corner",
      group: "exterior",
      title: "Front passenger corner",
      recommendedFirst: true,
      photo: null,
    },
    {
      angleKey: "dashboard_odometer",
      group: "interior",
      title: "Dashboard",
      recommendedFirst: false,
      photo: null,
    },
    {
      angleKey: "trunk_cargo",
      group: "detail",
      title: "Trunk",
      recommendedFirst: false,
      photo: null,
    },
    {
      angleKey: "extra-1",
      isExtra: true,
      title: "Damage",
      photo: { photoId: 2, fileUrl: "https://example.com/b.jpg" },
    },
  ],
};

describe("flattenStandardSlots", () => {
  it("orders exterior, interior, detail and excludes extras", () => {
    const flat = flattenStandardSlots(phase);
    expect(flat).toHaveLength(4);
    expect(flat[0].angleKey).toBe("front_driver_corner");
    expect(flat[1].group).toBe("exterior");
    expect(flat[2].group).toBe("interior");
    expect(flat[3].group).toBe("detail");
  });
});

describe("getStepMeta", () => {
  it("returns group and global indices", () => {
    const flat = flattenStandardSlots(phase);
    const meta = getStepMeta(2, flat);
    expect(meta.groupKey).toBe("interior");
    expect(meta.globalIndex).toBe(2);
    expect(meta.stepInGroup).toBe(0);
  });
});

describe("counts", () => {
  it("counts uploaded per group and recommended", () => {
    const flat = flattenStandardSlots(phase);
    expect(countUploadedInGroup(flat, "exterior")).toBe(1);
    expect(countUploadedInGroup(flat, "interior")).toBe(0);
    expect(countRecommendedUploaded(flat)).toBe(1);
  });
});

describe("findResumeStepIndex", () => {
  it("returns first missing photo index", () => {
    const flat = flattenStandardSlots(phase);
    expect(findResumeStepIndex(flat)).toBe(1);
  });
});

describe("isLastStepInGroup", () => {
  it("detects group boundary steps", () => {
    const flat = flattenStandardSlots(phase);
    expect(isLastStepInGroup(0, flat)).toBe(false);
    expect(isLastStepInGroup(1, flat)).toBe(true);
    expect(isLastStepInGroup(2, flat)).toBe(true);
  });
});
