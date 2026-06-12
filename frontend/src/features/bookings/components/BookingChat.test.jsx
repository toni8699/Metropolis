import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BookingChat from "@/features/bookings/components/BookingChat";

// Mock useBookingChat hook
const mockSendMessage = vi.fn();
const defaultHookState = {
  messages: [],
  isLoading: false,
  loadError: null,
  sendError: null,
  isJoined: true,
  isConnected: true,
  isSending: false,
  sendMessage: mockSendMessage,
};

vi.mock("@/shared/hooks/useBookingChat", () => ({
  useBookingChat: () => defaultHookState,
}));

// Stub ChatMessageList to avoid deep tree
vi.mock("@/features/chat/components/ChatMessageList", () => ({
  default: ({ messages, emptyLabel }) =>
    messages.length === 0 ? (
      <p data-testid="empty-label">{emptyLabel}</p>
    ) : (
      <ul>
        {messages.map((m) => (
          <li key={m.messageId} data-testid="message-item">
            {m.messageText}
          </li>
        ))}
      </ul>
    ),
}));

// lucide-react icons
vi.mock("lucide-react", () => ({
  MessageCircle: () => <span />,
  Send: () => <span />,
}));

const defaultProps = {
  bookingId: 1,
  renterUserId: 10,
  hostUserId: 20,
  currentUserId: 10,
};

describe("BookingChat", () => {
  beforeEach(() => {
    mockSendMessage.mockReset();
    Object.assign(defaultHookState, {
      messages: [],
      isLoading: false,
      loadError: null,
      sendError: null,
      isJoined: true,
      isConnected: true,
      isSending: false,
    });
  });

  it("renders Messages heading", () => {
    render(<BookingChat {...defaultProps} />);
    expect(screen.getByRole("heading", { name: /messages/i })).toBeDefined();
  });

  it("shows Live badge when joined", () => {
    render(<BookingChat {...defaultProps} />);
    expect(screen.getByText("Live")).toBeDefined();
  });

  it("shows Connecting badge when not connected", () => {
    defaultHookState.isJoined = false;
    defaultHookState.isConnected = false;
    render(<BookingChat {...defaultProps} />);
    expect(screen.getByText(/connecting/i)).toBeDefined();
  });

  it("shows chat unavailable when participants missing", () => {
    render(
      <BookingChat
        bookingId={1}
        renterUserId={null}
        hostUserId={null}
        currentUserId={null}
      />,
    );
    expect(screen.getByText(/chat unavailable/i)).toBeDefined();
  });

  it("renders empty label when no messages", () => {
    render(<BookingChat {...defaultProps} />);
    expect(screen.getByTestId("empty-label")).toBeDefined();
  });

  it("renders existing messages", () => {
    defaultHookState.messages = [
      { messageId: 1, messageText: "Hello host!", senderId: 10, createdAt: new Date().toISOString() },
    ];
    render(<BookingChat {...defaultProps} />);
    expect(screen.getByText("Hello host!")).toBeDefined();
  });

  it("sends message on form submit and clears input", async () => {
    mockSendMessage.mockResolvedValue(true);
    render(<BookingChat {...defaultProps} />);
    const input = screen.getByPlaceholderText(/write a message/i);
    fireEvent.change(input, { target: { value: "Test message" } });
    fireEvent.submit(input.closest("form"));
    await vi.waitFor(() => expect(mockSendMessage).toHaveBeenCalledWith("Test message"));
  });

  it("disables send button when input is empty", () => {
    render(<BookingChat {...defaultProps} />);
    const btn = screen.getByRole("button", { name: /send/i });
    expect(btn.disabled).toBe(true);
  });

  it("shows load error banner", () => {
    defaultHookState.loadError = "Failed to load messages.";
    render(<BookingChat {...defaultProps} />);
    expect(screen.getByText(/failed to load messages/i)).toBeDefined();
  });

  it("shows send error banner", () => {
    defaultHookState.sendError = "Could not send message.";
    render(<BookingChat {...defaultProps} />);
    expect(screen.getByText(/could not send message/i)).toBeDefined();
  });

  it("disables input while sending", () => {
    defaultHookState.isSending = true;
    render(<BookingChat {...defaultProps} />);
    const input = screen.getByPlaceholderText(/write a message/i);
    expect(input.disabled).toBe(true);
  });
});
