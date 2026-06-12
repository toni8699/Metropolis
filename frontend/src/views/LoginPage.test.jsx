import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LoginPage from "@/views/LoginPage";

const mockNavigate = vi.fn();
let mockAuth;

vi.mock("react-router-dom", async (importActual) => {
  const actual = await importActual();
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => mockAuth,
}));

vi.mock("@/layout/Layout", () => ({
  default: ({ children }) => <div>{children}</div>,
}));

vi.mock("@/shared/components/AuthModal", () => ({
  default: ({ isOpen, mode }) =>
    isOpen ? <div data-testid="auth-modal">{mode}</div> : null,
}));

function renderLogin(initialEntry = "/login?redirect_to=/app/account") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/app/account" element={<div>Account page</div>} />
        <Route path="/app" element={<div>App home</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  it("renders login modal when unauthenticated", () => {
    mockAuth = { isAuthenticated: false };
    renderLogin();
    expect(screen.getByTestId("auth-modal")).toBeDefined();
    expect(screen.getByText("login")).toBeDefined();
  });

  it("redirects authenticated users to redirect_to", () => {
    mockAuth = { isAuthenticated: true };
    renderLogin("/login?redirect_to=/app/account");
    expect(screen.getByText("Account page")).toBeDefined();
  });

  it("falls back to /app for invalid redirect_to", () => {
    mockAuth = { isAuthenticated: true };
    renderLogin("/login?redirect_to=https://evil.example");
    expect(screen.getByText("App home")).toBeDefined();
  });
});
