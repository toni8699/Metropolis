import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AuthModal from "@/shared/components/AuthModal";

const mockRegister = vi.fn();

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    login: vi.fn(),
    register: mockRegister,
    googleLogin: vi.fn(),
  }),
}));

vi.mock("lucide-react", () => ({
  X: () => <span />,
}));

describe("AuthModal", () => {
  beforeEach(() => {
    mockRegister.mockReset();
    mockRegister.mockResolvedValue({ status: "success" });
  });

  it("submits email and password during signup", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<AuthModal isOpen mode="signup" onClose={onClose} />);

    await user.type(screen.getByPlaceholderText(/email/i), "jane@example.com");
    await user.type(screen.getByPlaceholderText(/password/i), "Secret123!");
    await user.click(screen.getByRole("button", { name: /sign up/i }));

    await vi.waitFor(() =>
      expect(mockRegister).toHaveBeenCalledWith({
        email: "jane@example.com",
        password: "Secret123!",
      }),
    );
    expect(onClose).toHaveBeenCalled();
  });
});
