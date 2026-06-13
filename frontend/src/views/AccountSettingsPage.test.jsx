import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import AccountSettingsPage from "@/views/AccountSettingsPage";

const mockUpdateProfile = vi.fn();
let mockAuth;

vi.mock("@/context/AuthContext", () => ({
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
      lives: "",
      about: "",
      languages: "",
      work: "",
      tripsCount: 0,
      hasPhone: true,
      hasEmail: true,
      isApprovedToDrive: false,
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
        joinedLabel: "Joined June 2026",
        lives: "",
        about: "",
        languages: "",
        work: "",
        tripsCount: 0,
        hasPhone: false,
        hasEmail: true,
        isApprovedToDrive: false,
      },
    };
  });

  it("saves profile changes", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText(/phone/i), "+1 514 555 0100");
    await user.click(screen.getByRole("button", { name: /save profile/i }));

    await vi.waitFor(() =>
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        lives: "",
        about: "",
        languages: "",
        work: "",
        phone: "+1 514 555 0100",
      }),
    );
    expect(await screen.findByText(/profile updated/i)).toBeDefined();
  });

  it("redirects unauthenticated users to login with return path", () => {
    mockAuth = {
      isAuthenticated: false,
      updateProfile: mockUpdateProfile,
      user: null,
    };
    render(
      <MemoryRouter initialEntries={["/app/account"]}>
        <Routes>
          <Route path="/app/account" element={<AccountSettingsPage />} />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("Login page")).toBeDefined();
  });
});
