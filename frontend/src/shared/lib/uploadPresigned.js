import { apiPost } from "@/shared/api/api";

/** Presign → PUT to S3 → complete. Returns presign payload (incl. fileUrl when present). */
export async function uploadPresignedFile(file, { presignBody, completeBody }) {
  const presign = await apiPost("/api/uploads/presign", presignBody, true);
  const contentType = file.type || "application/octet-stream";
  const uploadResponse = await fetch(presign.presignedUrl, {
    method: "PUT",
    headers: { "Content-Type": contentType },
    body: file,
  });
  if (!uploadResponse.ok) {
    throw new Error(`Upload failed for ${file.name}.`);
  }
  await apiPost(
    "/api/uploads/complete",
    {
      ...completeBody,
      objectKey: presign.objectKey,
      contentType,
      sizeBytes: file.size,
    },
    true,
  );
  return presign;
}
