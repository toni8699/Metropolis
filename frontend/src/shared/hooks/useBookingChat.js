import { useCallback, useEffect, useState } from "react";
import { extractMessages, mergeMessages, normalizeMessage } from "@/shared/lib/chatMessages";
import {
  acquireBookingSocket,
  joinBookingRoom,
  leaveBookingRoom,
  releaseBookingSocket,
} from "@/shared/lib/socket";
import { apiGet, apiPost } from "@/shared/api/api";

const messageCacheByBooking = new Map();

export function useBookingChat(bookingId, currentUserId, { onMessage } = {}) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [sendError, setSendError] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isJoined, setIsJoined] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const appendMessage = useCallback((raw) => {
    const message = normalizeMessage(raw);
    if (!message) return;
    setMessages((prev) => {
      const next = mergeMessages(prev, [message]);
      const cacheKey = Number(message.bookingId);
      if (cacheKey) messageCacheByBooking.set(cacheKey, next);
      return next;
    });
    onMessage?.(message);
  }, [onMessage]);

  useEffect(() => {
    if (!bookingId) {
      setMessages([]);
      setIsLoading(false);
      return undefined;
    }

    let cancelled = false;
    const activeBookingId = Number(bookingId);
    const cached = messageCacheByBooking.get(activeBookingId);

    setLoadError("");
    if (cached) {
      setMessages(cached);
      setIsLoading(false);
    } else {
      setMessages([]);
      setIsLoading(true);
    }

    apiGet(`/api/bookings/${activeBookingId}/messages`, true)
      .then((data) => {
        if (cancelled) return;
        const next = mergeMessages([], extractMessages(data));
        messageCacheByBooking.set(activeBookingId, next);
        setMessages(next);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(err?.message || "Could not load messages.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [bookingId]);

  useEffect(() => {
    if (!bookingId || !currentUserId) {
      setIsConnected(false);
      setIsJoined(false);
      return undefined;
    }

    const socket = acquireBookingSocket();
    const activeBookingId = Number(bookingId);

    const onConnect = () => {
      setIsConnected(true);
      setSendError("");
      setIsJoined(false);
      joinBookingRoom(activeBookingId);
    };

    const onDisconnect = () => {
      setIsConnected(false);
      setIsJoined(false);
    };

    const onJoined = (payload) => {
      if (Number(payload?.bookingId) === activeBookingId) {
        setIsJoined(true);
        setSendError("");
      }
    };

    const onNewMessage = (message) => {
      const msgBookingId = Number(message?.bookingId ?? message?.booking_id);
      if (msgBookingId === activeBookingId) appendMessage(message);
    };

    const onChatError = (payload) => {
      setSendError(payload?.message || "Chat connection error.");
      setIsJoined(false);
    };

    const onConnectError = (err) => {
      setSendError(err?.message || "Could not connect to chat.");
      setIsConnected(false);
      setIsJoined(false);
    };

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("joined", onJoined);
    socket.on("new_message", onNewMessage);
    socket.on("chat_error", onChatError);
    socket.on("connect_error", onConnectError);

    if (socket.connected) {
      setIsConnected(true);
      joinBookingRoom(activeBookingId);
    }

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("joined", onJoined);
      socket.off("new_message", onNewMessage);
      socket.off("chat_error", onChatError);
      socket.off("connect_error", onConnectError);
      leaveBookingRoom();
      releaseBookingSocket();
    };
  }, [bookingId, currentUserId, appendMessage]);

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = String(text || "").trim();
      if (!trimmed || !bookingId) return false;

      setSendError("");
      setIsSending(true);
      try {
        const data = await apiPost(
          `/api/bookings/${bookingId}/messages`,
          { messageText: trimmed },
          true,
        );
        appendMessage(data?.message);
        return true;
      } catch (err) {
        setSendError(err?.message || "Could not send message.");
        return false;
      } finally {
        setIsSending(false);
      }
    },
    [bookingId, appendMessage],
  );

  return {
    messages,
    isLoading,
    loadError,
    sendError,
    isConnected,
    isJoined,
    isSending,
    sendMessage,
  };
}
