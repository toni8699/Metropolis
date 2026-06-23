import { describe, expect, it, vi, afterEach } from "vitest";
import { compressTripPhoto } from "@/shared/lib/compressTripPhoto";

describe("compressTripPhoto", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("rejects non-image files", async () => {
    const file = new File(["text"], "notes.txt", { type: "text/plain" });
    await expect(compressTripPhoto(file)).rejects.toThrow(/images/i);
  });

  it("rejects when image fails to load", async () => {
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:mock"),
      revokeObjectURL,
    });

    class BrokenImage {
      set src(_value) {
        queueMicrotask(() => this.onerror?.(new Event("error")));
      }
    }
    vi.stubGlobal("Image", BrokenImage);

    const file = new File(["bad"], "bad.jpg", { type: "image/jpeg" });
    await expect(compressTripPhoto(file)).rejects.toThrow(/read image/i);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock");
  });
});
