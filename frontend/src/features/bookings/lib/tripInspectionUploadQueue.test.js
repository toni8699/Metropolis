import { describe, expect, it, vi } from "vitest";
import { createTripInspectionUploadQueue } from "./tripInspectionUploadQueue";

vi.mock("@/features/bookings/lib/uploadTripInspectionPhoto", () => ({
  uploadTripInspectionPhoto: vi.fn(() => Promise.resolve({ objectKey: "k" })),
}));

vi.mock("@/features/bookings/lib/deleteTripInspectionPhoto", () => ({
  deleteTripInspectionPhoto: vi.fn(() => Promise.resolve()),
}));

import { uploadTripInspectionPhoto } from "@/features/bookings/lib/uploadTripInspectionPhoto";

describe("createTripInspectionUploadQueue", () => {
  it("enqueues and marks job done", async () => {
    const updates = [];
    const queue = createTripInspectionUploadQueue({
      bookingId: 1,
      onJobUpdate: (job) => updates.push(job.status),
      onJobDone: () => {},
    });

    const file = new File(["x"], "a.jpg", { type: "image/jpeg" });
    queue.enqueue({
      angleKey: "front_straight",
      file,
      phase: "CHECK_IN",
      localPreviewUrl: "blob:preview",
      isExtra: false,
    });

    await vi.waitFor(() => {
      expect(updates).toContain("done");
    });
    expect(uploadTripInspectionPhoto).toHaveBeenCalledWith(
      file,
      expect.objectContaining({
        angleKey: "front_straight",
        phase: "CHECK_IN",
        skipCompress: true,
      }),
    );
    expect(queue.pendingCount()).toBe(0);
  });

  it("marks job failed and retries", async () => {
    uploadTripInspectionPhoto.mockRejectedValueOnce(new Error("network"));
    uploadTripInspectionPhoto.mockResolvedValueOnce({ objectKey: "k" });

    const queue = createTripInspectionUploadQueue({
      bookingId: 1,
      onJobUpdate: () => {},
    });

    const file = new File(["x"], "b.jpg", { type: "image/jpeg" });
    const jobId = queue.enqueue({
      angleKey: "rear_straight",
      file,
      phase: "CHECK_IN",
      localPreviewUrl: "blob:preview2",
    });

    await vi.waitFor(() => {
      expect(queue.getJobForAngle("rear_straight", "CHECK_IN")?.status).toBe("failed");
    });

    queue.retry(jobId);
    await vi.waitFor(() => {
      expect(queue.getJobForAngle("rear_straight", "CHECK_IN")?.status).toBe("done");
    });
  });
});
