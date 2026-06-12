import { apiPost } from "@/shared/api/api";

export async function uploadProfilePhoto(file) {
  const presign = await apiPost(
    "/api/uploads/presign",
    {
      scope: "USER_AVATAR",
      fileName: file.name,
      contentType: file.type || "application/octet-stream",
    },
    true,
  );
  const uploadResponse = await fetch(presign.presignedUrl, {
    method: "PUT",
    headers: {
      "Content-Type": file.type || "application/octet-stream",
    },
    body: file,
  });
  if (!uploadResponse.ok) {
    throw new Error(`Upload failed for ${file.name}.`);
  }
  await apiPost(
    "/api/uploads/complete",
    {
      scope: "USER_AVATAR",
      objectKey: presign.objectKey,
      contentType: file.type || "application/octet-stream",
      sizeBytes: file.size,
    },
    true,
  );
  return presign.fileUrl;
}
