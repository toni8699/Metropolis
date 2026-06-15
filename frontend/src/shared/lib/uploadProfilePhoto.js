import { uploadPresignedFile } from "@/shared/lib/uploadPresigned";

export async function uploadProfilePhoto(file) {
  const presign = await uploadPresignedFile(file, {
    presignBody: {
      scope: "USER_AVATAR",
      fileName: file.name,
      contentType: file.type || "application/octet-stream",
    },
    completeBody: { scope: "USER_AVATAR" },
  });
  return presign.fileUrl;
}
