import { useState } from "react";
import { MessageCircle, Send } from "lucide-react";
import ChatMessageList from "@/features/chat/components/ChatMessageList";
import { useBookingChat } from "@/shared/hooks/useBookingChat";

export default function BookingChat({ bookingId, renterUserId, hostUserId, currentUserId }) {
  const [draft, setDraft] = useState("");
  const {
    messages,
    isLoading,
    loadError,
    sendError,
    isJoined,
    isConnected,
    isSending,
    sendMessage,
  } = useBookingChat(bookingId, currentUserId);

  const canChat = Boolean(renterUserId && hostUserId && currentUserId);

  const handleSend = async (event) => {
    event.preventDefault();
    const ok = await sendMessage(draft);
    if (ok) setDraft("");
  };

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-3 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-900">
          <MessageCircle className="h-4 w-4 text-indigo-600" />
          Messages
        </h2>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
            isJoined ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-600"
          }`}
        >
          {isJoined ? "Live" : isConnected ? "Joining…" : "Connecting…"}
        </span>
      </div>

      {!canChat ? (
        <p className="mt-3 text-sm text-gray-500">Chat unavailable for this trip.</p>
      ) : (
        <>
          {loadError && (
            <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{loadError}</p>
          )}

          <div
            className="mt-3 max-h-72 overflow-y-auto rounded-xl border border-gray-100 bg-gray-50 p-3"
            aria-live="polite"
            aria-label="Trip messages"
          >
            <ChatMessageList
              messages={messages}
              currentUserId={currentUserId}
              renterUserId={renterUserId}
              isLoading={isLoading}
              emptyLabel={`No messages yet. Say hello to your ${
                currentUserId === renterUserId ? "host" : "renter"
              }.`}
            />
          </div>

          {sendError && (
            <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">{sendError}</p>
          )}

          <form onSubmit={handleSend} className="mt-3 flex gap-2">
            <label htmlFor={`booking-chat-${bookingId}`} className="sr-only">
              Message
            </label>
            <input
              id={`booking-chat-${bookingId}`}
              type="text"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Write a message…"
              maxLength={4000}
              disabled={isSending}
              className="min-w-0 flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-100"
            />
            <button
              type="submit"
              disabled={!draft.trim() || isSending}
              className="inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              Send
            </button>
          </form>
        </>
      )}
    </section>
  );
}
