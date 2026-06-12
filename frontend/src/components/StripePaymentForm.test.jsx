import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import StripePaymentForm from "./StripePaymentForm";

// vi.hoisted ensures variables are available when vi.mock factory runs (mock hoisting)
const { mockConfirmPayment } = vi.hoisted(() => ({
  mockConfirmPayment: vi.fn(),
}));

vi.mock("@stripe/react-stripe-js", () => ({
  PaymentElement: () => <div data-testid="payment-element" />,
  useStripe: () => ({ confirmPayment: mockConfirmPayment }),
  useElements: () => ({}),
}));

describe("StripePaymentForm", () => {
  beforeEach(() => {
    mockConfirmPayment.mockReset();
  });

  it("renders the Pay now button", () => {
    render(<StripePaymentForm onSuccess={vi.fn()} onError={vi.fn()} />);
    expect(screen.getByRole("button", { name: /pay now/i })).toBeDefined();
  });

  it("renders the PaymentElement placeholder", () => {
    render(<StripePaymentForm onSuccess={vi.fn()} onError={vi.fn()} />);
    expect(screen.getByTestId("payment-element")).toBeDefined();
  });

  it("calls onSuccess when payment confirms without error", async () => {
    mockConfirmPayment.mockResolvedValue({ error: null });
    const onSuccess = vi.fn();
    const onError = vi.fn();
    render(<StripePaymentForm onSuccess={onSuccess} onError={onError} />);

    await act(async () => {
      fireEvent.submit(screen.getByRole("button", { name: /pay now/i }).closest("form"));
    });

    await vi.waitFor(() => expect(onSuccess).toHaveBeenCalledTimes(1));
    expect(onError).toHaveBeenCalledWith("");
  });

  it("calls onError with Stripe error message when payment fails", async () => {
    mockConfirmPayment.mockResolvedValue({ error: { message: "Card declined." } });
    const onSuccess = vi.fn();
    const onError = vi.fn();
    render(<StripePaymentForm onSuccess={onSuccess} onError={onError} />);

    await act(async () => {
      fireEvent.submit(screen.getByRole("button", { name: /pay now/i }).closest("form"));
    });

    await vi.waitFor(() =>
      expect(onError).toHaveBeenCalledWith(expect.stringMatching(/card declined/i)),
    );
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("calls onError when confirmPayment throws", async () => {
    mockConfirmPayment.mockRejectedValue(new Error("Network error"));
    const onSuccess = vi.fn();
    const onError = vi.fn();
    render(<StripePaymentForm onSuccess={onSuccess} onError={onError} />);

    await act(async () => {
      fireEvent.submit(screen.getByRole("button", { name: /pay now/i }).closest("form"));
    });

    await vi.waitFor(() =>
      expect(onError).toHaveBeenCalledWith(expect.stringMatching(/network error/i)),
    );
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("shows Processing text and disables button while in-flight", async () => {
    let resolve;
    mockConfirmPayment.mockReturnValue(new Promise((res) => (resolve = res)));
    const onSuccess = vi.fn();
    render(<StripePaymentForm onSuccess={onSuccess} onError={vi.fn()} />);
    const form = screen.getByRole("button", { name: /pay now/i }).closest("form");

    await act(async () => {
      fireEvent.submit(form);
    });

    const button = screen.getByRole("button");
    await vi.waitFor(() => expect(button.textContent).toMatch(/processing/i));
    expect(button.disabled).toBe(true);

    await act(async () => {
      resolve({ error: null });
    });
    await vi.waitFor(() => expect(onSuccess).toHaveBeenCalled());
  });
});
