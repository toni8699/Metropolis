import { buildGroupedPhase, GROUP_ORDER } from "./tripInspectionGroups";

/** Flatten standard (non-extra) slots into one linear train: exterior → interior → detail. */
export function flattenStandardSlots(phaseData) {
  const { groups } = buildGroupedPhase(phaseData);
  return GROUP_ORDER.flatMap((groupKey) => {
    const group = groups.find((entry) => entry.key === groupKey);
    return (group?.slots || []).map((slot) => ({ ...slot, group: groupKey }));
  });
}

export function getStepMeta(flatIndex, flatSlots) {
  const slot = flatSlots[flatIndex];
  const groupKey = slot?.group || GROUP_ORDER[0];
  const groupIndex = GROUP_ORDER.indexOf(groupKey);
  const groupSlots = flatSlots.filter((entry) => entry.group === groupKey);
  const stepInGroup = groupSlots.findIndex((entry) => entry.angleKey === slot?.angleKey);

  return {
    groupKey,
    groupIndex: groupIndex >= 0 ? groupIndex : 0,
    stepInGroup: stepInGroup >= 0 ? stepInGroup : 0,
    globalIndex: flatIndex,
    groupTotal: groupSlots.length,
    globalTotal: flatSlots.length,
  };
}

export function countUploadedInGroup(flatSlots, groupKey) {
  return flatSlots.filter(
    (slot) => slot.group === groupKey && Boolean(slot.photo?.fileUrl),
  ).length;
}

export function countRecommendedUploaded(flatSlots) {
  return flatSlots.filter(
    (slot) => slot.recommendedFirst && Boolean(slot.photo?.fileUrl),
  ).length;
}

/** First step missing a photo; if all filled, return 0. */
export function findResumeStepIndex(flatSlots) {
  const missing = flatSlots.findIndex((slot) => !slot.photo?.fileUrl);
  return missing >= 0 ? missing : 0;
}

export function firstStepIndexForGroup(flatSlots, groupKey) {
  const index = flatSlots.findIndex((slot) => slot.group === groupKey);
  return index >= 0 ? index : 0;
}

/** True when flatIndex is the last step within its group (triggers milestone pulse). */
export function isLastStepInGroup(flatIndex, flatSlots) {
  const meta = getStepMeta(flatIndex, flatSlots);
  return meta.stepInGroup === meta.groupTotal - 1;
}

export function groupMilestoneCounts(flatSlots) {
  return GROUP_ORDER.map((groupKey) => {
    const total = flatSlots.filter((slot) => slot.group === groupKey).length;
    const uploaded = countUploadedInGroup(flatSlots, groupKey);
    return { key: groupKey, total, uploaded };
  });
}
