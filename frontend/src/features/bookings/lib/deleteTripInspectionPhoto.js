import { apiDelete } from "@/shared/api/api";

export function deleteTripInspectionPhoto(bookingId, photoId) {
  return apiDelete(`/api/bookings/${bookingId}/inspection/photos/${photoId}`, true);
}
