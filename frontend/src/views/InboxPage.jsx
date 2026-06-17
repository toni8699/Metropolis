import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, CarFront, MessageCircle } from "lucide-react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import ChatComposer from "@/features/chat/components/ChatComposer";
import ChatMessageList from "@/features/chat/components/ChatMessageList";
import { useAuth } from "@/context/AuthContext";
import { useBookingChat } from "@/shared/hooks/useBookingChat";
import BodyCard from "@/shared/components/BodyCard";
import UserAvatar from "@/shared/components/UserAvatar";
import {
  formatInboxMessageTime,
  formatThreadContextSubtitle,
  tripPhaseLabel,
} from "@/shared/lib/inboxFormat";
import { bookingStatusBadgeClass, formatBookingStatusLabel } from "@/shared/lib/bookingStatus";
import { formatMoney, formatTripWindow } from "@/shared/lib/tripDetail";
import { apiGet } from "@/shared/api/api";

function ConversationListItem({ thread, isActive, onSelect }) {
  const otherName = thread.otherParty?.name || "Guest";
  const snippet = thread.latestMessage?.messageText || "";
  const timestamp = thread.latestMessage?.createdAt
    ? formatInboxMessageTime(thread.latestMessage.createdAt)
    : "";
  const unreadCount = Number(thread.unreadCount || 0);

  return (
    <button
      type="button"
      onClick={() => onSelect(thread.bookingId)}
      className={`flex w-full gap-3 border-b-2 border-black/10 px-4 py-4 text-left transition hover:bg-[#f5f5d0] ${
        isActive ? "border-l-4 border-l-[#E34B31] bg-[#f5f5d0]" : "border-l-4 border-l-transparent"
      }`}
    >
      <UserAvatar name={otherName} className="h-11 w-11 text-xs" />
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="truncate font-semibold text-gray-900">{otherName}</p>
          <div className="flex shrink-0 items-center gap-2">
            {unreadCount > 0 && (
              <span className="inline-flex min-w-[1.25rem] items-center justify-center rounded-full bg-[#E34B31] px-1.5 py-0.5 text-[10px] font-bold text-white">
                {unreadCount > 99 ? "99+" : unreadCount}
              </span>
            )}
            {timestamp && <span className="text-xs text-gray-500">{timestamp}</span>}
          </div>
        </div>
        <p className="mt-0.5 truncate text-sm text-gray-600">{snippet}</p>
        <p className="mt-1 truncate text-xs text-gray-500">
          {formatThreadContextSubtitle(thread)}
        </p>
      </div>
    </button>
  );
}

function ReservationSidebar({ thread }) {
  if (!thread) return null;

  const cover = thread.listing?.coverPhoto;

  return (
    <div className="space-y-4 p-5">
      <div className="overflow-hidden rounded-2xl border-2 border-black bg-[#dbe8be]">
        {cover ? (
          <img src={cover} alt={thread.listing?.title || "Vehicle"} className="h-40 w-full object-cover" />
        ) : (
          <div className="flex h-40 items-center justify-center text-gray-400">
            <CarFront className="h-10 w-10" />
          </div>
        )}
      </div>

      <div>
        <span
          className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${bookingStatusBadgeClass(thread.status)}`}
        >
          {formatBookingStatusLabel(thread.status)}
        </span>
        <h2 className="mt-3 text-lg font-semibold text-gray-900">
          {thread.listing?.title || "Reservation"}
        </h2>
        <p className="mt-1 text-sm text-gray-600">{formatTripWindow(thread.startAt, thread.endAt)}</p>
        {thread.cityZone && (
          <p className="mt-1 text-sm text-gray-500 capitalize">
            {thread.cityZone.replace(/-/g, " ")}
          </p>
        )}
      </div>

      {thread.pricing && (
        <dl className="space-y-2 rounded-2xl border-2 border-black bg-[#FCFCE5] p-4 text-sm">
          <div className="flex justify-between gap-3">
            <dt className="text-gray-600">Daily rate</dt>
            <dd className="font-medium text-gray-900">
              {formatMoney(thread.pricing.pricePerDay, thread.pricing.currency)}
            </dd>
          </div>
          {thread.pricing.total > 0 && (
            <div className="flex justify-between gap-3 border-t border-gray-100 pt-2">
              <dt className="font-semibold text-gray-900">Total</dt>
              <dd className="font-semibold text-gray-900">
                {formatMoney(thread.pricing.total, thread.pricing.currency)}
              </dd>
            </div>
          )}
        </dl>
      )}

      <Link
        to={`/app/bookings/${thread.bookingId}`}
        className="block rounded-full border-2 border-black border-b-4 bg-[#E34B31] px-4 py-2.5 text-center text-sm font-extrabold text-white active:border-b-0"
      >
        View full reservation details
      </Link>
    </div>
  );
}

export default function InboxPage() {
  const { isAuthenticated, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [threads, setThreads] = useState([]);
  const [isLoadingThreads, setIsLoadingThreads] = useState(true);
  const [threadsError, setThreadsError] = useState("");
  const [draft, setDraft] = useState("");
  const [mobilePane, setMobilePane] = useState("list");
  const scrollRef = useRef(null);

  const selectedBookingId = Number(searchParams.get("booking") || 0) || null;
  const selectedThread = useMemo(
    () => threads.find((thread) => thread.bookingId === selectedBookingId) || null,
    [threads, selectedBookingId],
  );

  useEffect(() => {
    if (!selectedBookingId || isLoadingThreads) return;
    if (!threads.some((thread) => thread.bookingId === selectedBookingId)) {
      setSearchParams({});
      setMobilePane("list");
    }
  }, [selectedBookingId, threads, isLoadingThreads, setSearchParams]);

  const loadThreads = useCallback(async ({ silent = false } = {}) => {
    if (!silent) {
      setThreadsError("");
      setIsLoadingThreads(true);
    }
    try {
      const data = await apiGet("/api/messages/threads", true);
      setThreads(data?.threads || []);
    } catch (err) {
      if (!silent) {
        setThreads([]);
        setThreadsError(err?.message || "Could not load conversations.");
      }
    } finally {
      if (!silent) setIsLoadingThreads(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    loadThreads();
  }, [isAuthenticated, loadThreads]);

  const handleThreadMessage = useCallback((message) => {
    setThreads((prev) => {
      const msgBookingId = Number(message.bookingId);
      const isFromMe = Number(message.senderId) === Number(user?.userId);
      const isActiveThread = Number(selectedBookingId) === msgBookingId;

      const next = prev.map((thread) => {
        if (thread.bookingId !== msgBookingId) return thread;
        let unreadCount = Number(thread.unreadCount || 0);
        if (isActiveThread) {
          unreadCount = 0;
        } else if (!isFromMe) {
          unreadCount += 1;
        }
        return {
          ...thread,
          unreadCount,
          latestMessage: {
            messageText: message.messageText,
            createdAt: message.createdAt,
          },
        };
      });
      return next.sort((a, b) => {
        const at = new Date(a.latestMessage?.createdAt || a.startAt).getTime();
        const bt = new Date(b.latestMessage?.createdAt || b.startAt).getTime();
        return bt - at;
      });
    });
  }, [selectedBookingId, user?.userId]);

  const {
    messages,
    isLoading: isLoadingMessages,
    loadError,
    sendError,
    isJoined,
    isSending,
    sendMessage,
  } = useBookingChat(selectedBookingId, user?.userId, { onMessage: handleThreadMessage });

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, selectedBookingId]);

  useEffect(() => {
    if (!selectedBookingId || isLoadingMessages) return;
    loadThreads({ silent: true });
  }, [selectedBookingId, isLoadingMessages, loadThreads]);

  const selectThread = (bookingId) => {
    setSearchParams({ booking: String(bookingId) });
    setMobilePane("chat");
    setDraft("");
    setThreads((prev) =>
      prev.map((thread) =>
        thread.bookingId === bookingId ? { ...thread, unreadCount: 0 } : thread,
      ),
    );
  };

  const handleSend = async (event) => {
    event.preventDefault();
    const ok = await sendMessage(draft);
    if (ok) setDraft("");
  };

  if (!isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  const otherName = selectedThread?.otherParty?.name || "Guest";

  return (
    <BodyCard className="grid h-[calc(100dvh-var(--app-header-offset)-var(--app-content-gap)*2-9rem)] max-h-[calc(100dvh-var(--app-header-offset)-var(--app-content-gap)*2-9rem)] grid-cols-1 grid-rows-1 overflow-hidden md:grid-cols-12">
      <aside
        className={`col-span-12 flex min-h-0 flex-col border-r-2 border-black md:col-span-3 ${
          mobilePane === "chat" ? "hidden md:flex" : "flex"
        }`}
      >
        <div className="shrink-0 border-b-2 border-black px-4 py-4">
          <h1 className="flex items-center gap-2 text-2xl font-extrabold text-[#183B1E]">
            <MessageCircle className="h-6 w-6 text-[#E34B31]" />
            Messages
          </h1>
        </div>

        {threadsError && (
          <p className="mx-4 mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{threadsError}</p>
        )}

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          {isLoadingThreads ? (
            <div className="space-y-3 p-4">
              {Array.from({ length: 4 }).map((_, idx) => (
                <div key={idx} className="h-16 animate-pulse rounded-xl bg-gray-100" />
              ))}
            </div>
          ) : threads.length === 0 ? (
            <div className="p-6 text-center text-sm text-gray-500">
              No conversations yet. Send a message from a trip page to start chatting.
            </div>
          ) : (
            threads.map((thread) => (
              <ConversationListItem
                key={thread.bookingId}
                thread={thread}
                isActive={thread.bookingId === selectedBookingId}
                onSelect={selectThread}
              />
            ))
          )}
        </div>
      </aside>

      <section
        className={`col-span-12 flex min-h-0 flex-col md:col-span-6 ${
          mobilePane === "list" ? "hidden md:flex" : "flex"
        }`}
      >
        {!selectedThread ? (
            <div className="flex flex-1 flex-col items-center justify-center px-6 text-center text-[#35593b]">
            <MessageCircle className="mb-3 h-10 w-10 text-gray-300" />
            <p className="text-sm">Select a conversation to start messaging</p>
          </div>
        ) : (
          <>
            <div className="flex shrink-0 items-center gap-3 border-b-2 border-black px-4 py-3">
              <button
                type="button"
                onClick={() => setMobilePane("list")}
                className="rounded-full p-1.5 text-gray-600 hover:bg-gray-100 md:hidden"
                aria-label="Back to conversations"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <UserAvatar name={otherName} className="h-10 w-10 text-xs" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold text-gray-900">{otherName}</p>
                <p className="truncate text-xs text-gray-500">
                  {selectedThread.listing?.title} · {tripPhaseLabel(selectedThread.status)}
                </p>
              </div>
              <span
                className={`hidden rounded-full px-2 py-0.5 text-[10px] font-semibold sm:inline ${
                  isJoined ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-600"
                }`}
              >
                {isJoined ? "Live" : "Connecting…"}
              </span>
            </div>

            {loadError && (
              <p className="mx-4 mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{loadError}</p>
            )}

            <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto overscroll-contain bg-[#f5f5d0] px-4 py-4">
              <ChatMessageList
                messages={messages}
                currentUserId={user?.userId}
                renterUserId={selectedThread.renterUserId}
                isLoading={isLoadingMessages}
                emptyLabel={`Say hello to ${otherName}.`}
              />
            </div>

            {sendError && (
              <p className="mx-4 shrink-0 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">{sendError}</p>
            )}

            <ChatComposer
              inputId="inbox-message"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onSubmit={handleSend}
              isSending={isSending}
              className="flex shrink-0 gap-2 border-t-2 border-black bg-[#FCFCE5] px-4 py-3"
              buttonClassName="inline-flex items-center gap-1 rounded-full border-2 border-black border-b-4 bg-[#E34B31] px-4 py-2 text-sm font-extrabold text-white active:border-b-0 disabled:opacity-50"
            />
          </>
        )}
      </section>

      <aside className="hidden min-h-0 overflow-y-auto overscroll-contain border-l-2 border-black lg:col-span-3 lg:block">
        <ReservationSidebar thread={selectedThread} />
      </aside>
    </BodyCard>
  );
}
