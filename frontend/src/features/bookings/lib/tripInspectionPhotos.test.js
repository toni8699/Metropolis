import { describe, expect, it } from "vitest";
import { collectPhasePhotos } from "./tripInspectionPhotos";

describe("collectPhasePhotos", () => {
  it("returns standard and extra uploads with labels", () => {
    const photos = collectPhasePhotos({
      slots: [
        {
          angleKey: "front_straight",
          title: "Front",
          photo: { photoId: 1, fileUrl: "https://example.com/a.jpg" },
        },
        {
          angleKey: "extra-1",
          isExtra: true,
          title: "Damage",
          photo: { photoId: 2, fileUrl: "https://example.com/b.jpg" },
        },
        { angleKey: "rear_straight", title: "Rear", photo: null },
      ],
    });
    expect(photos).toHaveLength(2);
    expect(photos[0].label).toBe("Front");
    expect(photos[1].label).toBe("Extra");
  });
});
