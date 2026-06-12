import { formatMessageTime } from "@/shared/lib/chatMessages";

export default function ChatMessageList({
  messages,
  currentUserId,
  renterUserId,
  isLoading,
  emptyLabel = "No messages yet.",
  className = "",
}) {
  if (isLoading && messages.length === 0) {
    return <p className="text-center text-sm text-gray-500">Loading messages…</p>;
  }

  if (messages.length === 0) {
    return <p className="text-center text-sm text-gray-500">{emptyLabel}</p>;
  }

  return (
    <div className={`space-y-3 ${className}`.trim()}>
      {messages.map((message) => {
        const isMyMessage = Number(message.senderId) === Number(currentUserId);
        const isFromRenter = Number(message.senderId) === Number(renterUserId);
        const senderLabel = isMyMessage
          ? "You"
          : message.senderName || (isFromRenter ? "Renter" : "Host");

        return (
          <div
            key={message.messageId}
            className={`flex ${isMyMessage ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`flex max-w-[75%] flex-col ${
                isMyMessage ? "items-end" : "items-start"
              }`}
            >
              <p
                className={`mb-1 text-[10px] font-semibold text-gray-500 ${
                  isMyMessage ? "text-right" : "text-left"
                }`}
              >
                {senderLabel}
              </p>
              <div
                className={
                  isMyMessage
                    ? "rounded-lg rounded-tr-none bg-blue-600 px-4 py-2.5 text-white shadow-sm"
                    : "rounded-lg rounded-tl-none bg-gray-100 px-4 py-2.5 text-gray-900 shadow-sm"
                }
              >
                <p className="whitespace-pre-wrap break-words text-sm">{message.messageText}</p>
                <p
                  className={`mt-1 text-[10px] ${
                    isMyMessage ? "text-blue-100" : "text-gray-500"
                  }`}
                >
                  {formatMessageTime(message.createdAt)}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
