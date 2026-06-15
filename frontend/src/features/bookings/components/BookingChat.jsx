import { useState } from "react";
import { MessageCircle } from "lucide-react";
import ChatComposer from "@/features/chat/components/ChatComposer";
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
    <section className="rounded-3xl border-2 border-black bg-[#FCFCE5] p-4 shadow-[6px_6px_0px_0px_rgba(24,59,30,0.35)]">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-lg font-extrabold text-[#183B1E]">
          <MessageCircle className="h-5 w-5 text-[#E34B31]" />
          Messages
        </h2>
        <span
          className={`rounded-full border-2 border-black px-2.5 py-0.5 text-[10px] font-bold ${
            isJoined ? "bg-[#dbe8be] text-[#183B1E]" : "bg-white text-[#35593b]"
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
            className="mt-3 max-h-72 overflow-y-auto rounded-2xl border-2 border-black bg-[#f5f5d0] p-3"
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

          <ChatComposer
            inputId={`booking-chat-${bookingId}`}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onSubmit={handleSend}
            isSending={isSending}
          />
        </>
      )}
    </section>
  );
}
