import { apiPost } from "@/shared/api/api";
import { compressTripPhoto } from "@/shared/lib/compressTripPhoto";

export async function uploadTripInspectionPhoto(
  file,
  { bookingId, phase, angleKey, isExtra, skipCompress = false },
) {
  const compressed = skipCompress ? file : await compressTripPhoto(file);
  const presignBody = {
    fileName: compressed.name,
    contentType: compressed.type || "image/jpeg",
    scope: "TRIP_INSPECTION",
    bookingId,
    phase,
    isExtra: Boolean(isExtra),
  };
  if (!isExtra && angleKey) {
    presignBody.angleKey = angleKey;
  }

  const presign = await apiPost("/api/uploads/presign", presignBody, true);
  const uploadResponse = await fetch(presign.presignedUrl, {
    method: "PUT",
    headers: { "Content-Type": compressed.type || "image/jpeg" },
    body: compressed,
  });
  if (!uploadResponse.ok) {
    throw new Error("Upload failed. Please try again.");
  }

  const completeBody = {
    ...presignBody,
    objectKey: presign.objectKey,
    contentType: compressed.type || "image/jpeg",
    sizeBytes: compressed.size,
  };
  if (!isExtra && angleKey) {
    completeBody.angleKey = angleKey;
  }

  await apiPost("/api/uploads/complete", completeBody, true);
  return presign;
}
