import { useCallback, useRef, useState } from "react";
import { createTripInspectionUploadQueue } from "@/features/bookings/lib/tripInspectionUploadQueue";

export function useTripInspectionUploadQueue({ bookingId, onJobDone, onJobFailed }) {
  const [, bump] = useState(0);
  const onJobDoneRef = useRef(onJobDone);
  const onJobFailedRef = useRef(onJobFailed);
  const queueRef = useRef(null);
  const bookingIdRef = useRef(bookingId);

  onJobDoneRef.current = onJobDone;
  onJobFailedRef.current = onJobFailed;

  if (!queueRef.current || bookingIdRef.current !== bookingId) {
    bookingIdRef.current = bookingId;
    queueRef.current = createTripInspectionUploadQueue({
      bookingId,
      onJobUpdate: () => bump((n) => n + 1),
      onJobDone: (job) => onJobDoneRef.current?.(job),
      onJobFailed: (job) => onJobFailedRef.current?.(job),
    });
  }

  const queue = queueRef.current;

  const enqueue = useCallback((payload) => queue.enqueue(payload), [queue]);
  const retry = useCallback((jobId) => queue.retry(jobId), [queue]);
  const getJobForAngle = useCallback(
    (angleKey, phase) => queue.getJobForAngle(angleKey, phase),
    [queue],
  );
  const getJobsForPhase = useCallback((phase) => queue.getJobsForPhase(phase), [queue]);
  const clearJobForAngle = useCallback(
    (angleKey, phase) => queue.clearJobForAngle(angleKey, phase),
    [queue],
  );
  const clearJob = useCallback((jobId) => queue.clearJob(jobId), [queue]);
  const finalizeJob = useCallback(
    (angleKey, phase) => queue.finalizeJob(angleKey, phase),
    [queue],
  );
  const getLocalPreview = useCallback(
    (angleKey, phase) => queue.getLocalPreview(angleKey, phase),
    [queue],
  );

  return {
    enqueue,
    retry,
    getJobForAngle,
    getJobsForPhase,
    clearJobForAngle,
    clearJob,
    finalizeJob,
    getLocalPreview,
    pendingCount: queue.pendingCount(),
  };
}
