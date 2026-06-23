export const GROUP_ORDER = ["exterior", "interior", "detail"];

export const GROUP_LABELS = {
  exterior: "Exterior",
  interior: "Interior",
  detail: "Details",
};

/** Group standard slots from inspection API (manifest lives on backend only). */
export function buildGroupedPhase(phaseData) {
  const slots = phaseData?.slots || [];
  const extras = slots.filter((slot) => slot.isExtra);
  const standard = slots.filter((slot) => !slot.isExtra);

  const groups = GROUP_ORDER.map((groupKey) => ({
    key: groupKey,
    label: GROUP_LABELS[groupKey] || groupKey,
    slots: standard.filter((slot) => slot.group === groupKey),
  }));

  return { groups, extras };
}
