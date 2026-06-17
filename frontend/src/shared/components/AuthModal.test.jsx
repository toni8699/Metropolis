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
    mockRegister.mockResolvedValue({
      status: "success",
      token: "test-token",
      user: { email: "jane@example.com", isVerified: false },
    });
  });

  it("submits email, password, and full name during signup", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<AuthModal isOpen mode="signup" onClose={onClose} />);

    await user.type(screen.getByPlaceholderText(/full name/i), "Jane Doe");
    await user.type(screen.getByPlaceholderText(/email/i), "jane@example.com");
    await user.type(screen.getByPlaceholderText(/password/i), "Secret123!");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /sign up/i }));

    await vi.waitFor(() =>
      expect(mockRegister).toHaveBeenCalledWith({
        email: "jane@example.com",
        password: "Secret123!",
        fullName: "Jane Doe",
      }),
    );
    expect(onClose).toHaveBeenCalled();
  });

  it("keeps sign up disabled until terms, name, and password are valid", () => {
    render(<AuthModal isOpen mode="signup" onClose={vi.fn()} />);
    expect(screen.getByRole("button", { name: /sign up/i })).toHaveProperty("disabled", true);
  });
});
