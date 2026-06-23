/** Collect uploaded photos for one inspection phase (standard + extras). */
export function collectPhasePhotos(phaseData) {
  const slots = phaseData?.slots || [];
  return slots
    .filter((slot) => slot.photo?.fileUrl)
    .map((slot) => ({
      photoId: slot.photo.photoId,
      fileUrl: slot.photo.fileUrl,
      label: slot.isExtra ? "Extra" : slot.title,
      angleKey: slot.angleKey,
      isExtra: Boolean(slot.isExtra),
    }));
}
