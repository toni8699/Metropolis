import { describe, expect, it } from "vitest";
import { listingCoords, parseCoord } from "@/shared/lib/location";

describe("parseCoord", () => {
  it("parses numbers and locale decimal strings", () => {
    expect(parseCoord(43.65)).toBe(43.65);
    expect(parseCoord("43,65")).toBe(43.65);
    expect(parseCoord(null)).toBeNull();
  });
});

describe("listingCoords", () => {
  it("reads lat/lng aliases", () => {
    expect(listingCoords({ lat: 1, lng: 2 })).toEqual({ lat: 1, lng: 2 });
    expect(listingCoords({ latitude: "45,5", longitude: "-73.5" })).toEqual({
      lat: 45.5,
      lng: -73.5,
    });
    expect(listingCoords({})).toBeNull();
  });
});
