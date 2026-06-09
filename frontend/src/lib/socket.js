import { io } from "socket.io-client";
import { getAccessToken } from "../utils/api";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

let sharedSocket = null;
let refCount = 0;
let activeBookingId = null;

function createSocketInstance() {
  return io(API_BASE, {
    autoConnect: false,
    auth: { token: getAccessToken() },
    transports: ["websocket", "polling"],
    reconnection: true,
  });
}

export function acquireBookingSocket() {
  if (!sharedSocket) {
    sharedSocket = createSocketInstance();
    sharedSocket.connect();
  }
  refCount += 1;
  return sharedSocket;
}

export function releaseBookingSocket() {
  refCount = Math.max(0, refCount - 1);
  if (refCount === 0 && sharedSocket) {
    if (activeBookingId != null) {
      sharedSocket.emit("leave_room", { bookingId: activeBookingId });
      activeBookingId = null;
    }
    sharedSocket.disconnect();
    sharedSocket = null;
  }
}

export function joinBookingRoom(bookingId) {
  if (!sharedSocket) return;
  const id = Number(bookingId);
  if (activeBookingId != null && activeBookingId !== id) {
    sharedSocket.emit("leave_room", { bookingId: activeBookingId });
  }
  activeBookingId = id;
  sharedSocket.emit("join_room", { bookingId: id });
}

export function leaveBookingRoom() {
  if (!sharedSocket || activeBookingId == null) return;
  sharedSocket.emit("leave_room", { bookingId: activeBookingId });
  activeBookingId = null;
}
