import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import AccountSettingsPage from "./AccountSettingsPage";

const mockUpdateProfile = vi.fn();
let mockAuth;

vi.mock("../context/AuthContext", () => ({
  useAuth: () => mockAuth,
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <AccountSettingsPage />
    </MemoryRouter>,
  );
}

describe("AccountSettingsPage", () => {
  beforeEach(() => {
    mockUpdateProfile.mockReset();
    mockUpdateProfile.mockResolvedValue({
      fullName: "Jane Driver",
      phone: "+1 514 555 0100",
    });
    mockAuth = {
      isAuthenticated: true,
      updateProfile: mockUpdateProfile,
      user: {
        userId: 1,
        email: "jane@example.com",
        fullName: "Jane Driver",
        phone: "",
        role: "user",
        createdAt: "2026-06-01T12:00:00Z",
      },
    };
  });

  it("saves profile changes", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText(/phone/i), "+1 514 555 0100");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await vi.waitFor(() =>
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        fullName: "Jane Driver",
        phone: "+1 514 555 0100",
      }),
    );
    expect(await screen.findByText(/profile updated/i)).toBeDefined();
  });
});
