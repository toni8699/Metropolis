const MAX_EDGE = 1920;
const JPEG_QUALITY = 0.8;

/**
 * Resize image via canvas; rejects on load error. Revokes object URL after draw.
 * @param {File} file
 * @returns {Promise<File>}
 */
export function compressTripPhoto(file) {
  if (!file.type.startsWith("image/")) {
    return Promise.reject(new Error("Inspection photos must be images."));
  }

  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Could not read image. Try another photo."));
    };

    img.onload = () => {
      URL.revokeObjectURL(objectUrl);
      try {
        let { width, height } = img;
        const maxEdge = Math.max(width, height);
        if (maxEdge > MAX_EDGE) {
          const scale = MAX_EDGE / maxEdge;
          width = Math.round(width * scale);
          height = Math.round(height * scale);
        }

        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          reject(new Error("Could not process image."));
          return;
        }
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error("Could not compress image."));
              return;
            }
            const base = file.name.replace(/\.[^.]+$/, "") || "inspection";
            resolve(new File([blob], `${base}.jpg`, { type: "image/jpeg" }));
          },
          "image/jpeg",
          JPEG_QUALITY,
        );
      } catch (err) {
        reject(err instanceof Error ? err : new Error("Could not process image."));
      }
    };

    img.src = objectUrl;
  });
}
