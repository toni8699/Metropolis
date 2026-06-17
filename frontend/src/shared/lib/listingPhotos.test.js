import { describe, expect, it } from "vitest";
import { nextWeekendRange } from "@/shared/lib/weekendDates";
import { listingPhotos } from "@/shared/lib/listingPhotos";

describe("nextWeekendRange", () => {
  it("returns saturday and sunday pair", () => {
    const { saturday, sunday } = nextWeekendRange();
    expect(sunday.getTime() - saturday.getTime()).toBe(24 * 60 * 60 * 1000);
    expect(saturday.getDay()).toBe(6);
    expect(sunday.getDay()).toBe(0);
  });
});

describe("listingPhotos", () => {
  it("dedupes gallery and pads grid to five slots", () => {
    const { grid, gallery } = listingPhotos({
      photos: ["a.jpg", "b.jpg"],
      images: ["b.jpg", "c.jpg"],
    });
    expect(gallery).toEqual(["b.jpg", "c.jpg", "a.jpg"]);
    expect(grid).toEqual(["a.jpg", "b.jpg", "a.jpg", "b.jpg", "a.jpg"]);
  });
});
