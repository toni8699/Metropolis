function createImage(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener("load", () => resolve(image));
    image.addEventListener("error", () => reject(new Error("Failed to load image for cropping.")));
    image.setAttribute("crossOrigin", "anonymous");
    image.src = url;
  });
}

/**
 * Draw the cropped region onto a canvas and export as a JPEG Blob.
 * @param {string} imageSrc - Data URL or image URL
 * @param {{ x: number, y: number, width: number, height: number }} pixelCrop
 * @param {number} quality - JPEG quality 0–1
 */
export async function getCroppedImageBlob(imageSrc, pixelCrop, quality = 0.92) {
  if (!pixelCrop?.width || !pixelCrop?.height) {
    throw new Error("Invalid crop area.");
  }

  const image = await createImage(imageSrc);
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Canvas is not supported in this browser.");
  }

  canvas.width = pixelCrop.width;
  canvas.height = pixelCrop.height;

  ctx.drawImage(
    image,
    pixelCrop.x,
    pixelCrop.y,
    pixelCrop.width,
    pixelCrop.height,
    0,
    0,
    pixelCrop.width,
    pixelCrop.height,
  );

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error("Failed to export cropped image."));
          return;
        }
        resolve(blob);
      },
      "image/jpeg",
      quality,
    );
  });
}
