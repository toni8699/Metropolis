export function formatMessageTime(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function normalizeMessage(raw) {
  if (!raw) return null;
  const messageId = raw.messageId ?? raw.message_id;
  if (messageId == null) return null;
  return {
    messageId: Number(messageId),
    bookingId: Number(raw.bookingId ?? raw.booking_id ?? 0),
    senderId: Number(raw.senderId ?? raw.sender_id),
    senderName: raw.senderName ?? raw.sender_name ?? null,
    messageText: String(raw.messageText ?? raw.message_text ?? ""),
    createdAt: raw.createdAt ?? raw.created_at ?? "",
  };
}

export function extractMessages(data) {
  if (Array.isArray(data?.messages)) return data.messages;
  if (data?.message) return [data.message];
  return [];
}

export function mergeMessages(existing, incoming) {
  const byId = new Map();
  for (const item of [...existing, ...incoming]) {
    const normalized = normalizeMessage(item);
    if (normalized) byId.set(normalized.messageId, normalized);
  }
  return Array.from(byId.values()).sort((a, b) => {
    const at = new Date(a.createdAt).getTime() || 0;
    const bt = new Date(b.createdAt).getTime() || 0;
    if (at !== bt) return at - bt;
    return a.messageId - b.messageId;
  });
}
