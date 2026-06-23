import { deleteTripInspectionPhoto } from "@/features/bookings/lib/deleteTripInspectionPhoto";
import { uploadTripInspectionPhoto } from "@/features/bookings/lib/uploadTripInspectionPhoto";

// ponytail: in-memory queue only; refresh page loses pending — upgrade: IndexedDB

let nextJobId = 1;

function revokePreview(job) {
  if (job?.localPreviewUrl?.startsWith("blob:")) {
    URL.revokeObjectURL(job.localPreviewUrl);
  }
}

export function createTripInspectionUploadQueue({ bookingId, onJobUpdate, onJobDone, onJobFailed }) {
  const jobs = new Map();
  let processing = false;

  const emit = (job) => {
    onJobUpdate?.(job);
    jobs.set(job.id, job);
  };

  const processNext = async () => {
    if (processing) return;
    const pending = [...jobs.values()].find((job) => job.status === "queued");
    if (!pending) return;

    processing = true;
    const job = { ...pending, status: "uploading" };
    emit(job);

    try {
      if (job.replacePhotoId) {
        await deleteTripInspectionPhoto(bookingId, job.replacePhotoId);
      }
      await uploadTripInspectionPhoto(job.file, {
        bookingId,
        phase: job.phase,
        angleKey: job.angleKey,
        isExtra: Boolean(job.isExtra),
        skipCompress: true,
      });
      const done = { ...job, status: "done" };
      emit(done);
      onJobDone?.(done);
    } catch (err) {
      const failed = {
        ...job,
        status: "failed",
        error: err?.message || "Upload failed.",
      };
      emit(failed);
      onJobFailed?.(failed);
    } finally {
      processing = false;
      processNext();
    }
  };

  return {
    enqueue({ angleKey, file, phase, localPreviewUrl, replacePhotoId, isExtra = false, label }) {
      const existing = [...jobs.values()].find(
        (job) =>
          job.angleKey === angleKey &&
          job.phase === phase &&
          (job.status === "queued" || job.status === "uploading"),
      );
      if (existing) return existing.id;

      const id = `job-${nextJobId++}`;
      const job = {
        id,
        angleKey,
        file,
        phase,
        localPreviewUrl,
        replacePhotoId,
        isExtra,
        label: label || null,
        status: "queued",
        error: null,
      };
      emit(job);
      processNext();
      return id;
    },

    retry(jobId) {
      const job = jobs.get(jobId);
      if (!job || job.status !== "failed") return;
      emit({ ...job, status: "queued", error: null });
      processNext();
    },

    getJobForAngle(angleKey, phase) {
      return [...jobs.values()].find(
        (job) => job.angleKey === angleKey && job.phase === phase,
      );
    },

    getJobsForPhase(phase) {
      return [...jobs.values()].filter((job) => job.phase === phase);
    },

    clearJobForAngle(angleKey, phase) {
      const job = this.getJobForAngle(angleKey, phase);
      if (!job) return;
      revokePreview(job);
      jobs.delete(job.id);
      onJobUpdate?.();
    },

    clearJob(jobId) {
      const job = jobs.get(jobId);
      if (!job) return;
      revokePreview(job);
      jobs.delete(jobId);
      onJobUpdate?.();
    },

    /** Drop local blob once API has the server URL. */
    finalizeJob(angleKey, phase) {
      const job = this.getJobForAngle(angleKey, phase);
      if (!job || job.status !== "done") return;
      revokePreview(job);
      jobs.delete(job.id);
      onJobUpdate?.();
    },

    getLocalPreview(angleKey, phase) {
      const job = this.getJobForAngle(angleKey, phase);
      if (!job || job.status === "failed") return null;
      return job.localPreviewUrl || null;
    },

    pendingCount() {
      return [...jobs.values()].filter(
        (job) => job.status === "queued" || job.status === "uploading",
      ).length;
    },
  };
}
