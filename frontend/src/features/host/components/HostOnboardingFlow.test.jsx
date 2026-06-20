import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import HostOnboardingFlow from "@/features/host/components/HostOnboardingFlow";

vi.mock("@/context/GoogleMapsProvider", () => ({
  useGoogleMaps: () => ({ isLoaded: true, loadError: null, apiKey: "test-key" }),
}));

vi.mock("@/features/host/constants", () => ({ MIN_LISTING_PHOTOS: 1 }));

vi.mock("@/shared/lib/placesAutocomplete", () => ({
  fetchPlacePredictions: vi.fn().mockResolvedValue([]),
  resolvePredictionCoordinates: vi.fn().mockResolvedValue({ lat: 45.5, lng: -73.5 }),
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importActual) => {
  const actual = await importActual();
  return { ...actual, useNavigate: () => mockNavigate };
});

const mockRefreshMe = vi.fn();
const mockEnsureVerifiedEmail = vi.fn(() => true);
vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    refreshMe: mockRefreshMe,
    ensureVerifiedEmail: mockEnsureVerifiedEmail,
  }),
}));

vi.mock("@/shared/api/api", () => ({
  apiGet: vi.fn().mockResolvedValue({
    bodyTypes: [
      { bodyTypeId: 1, code: "SEDAN", displayName: "Sedan" },
      { bodyTypeId: 8, code: "OTHER", displayName: "Other" },
    ],
  }),
  apiPost: vi.fn().mockImplementation((path) => {
    if (String(path).includes("/vin/decode")) {
      return Promise.resolve({
        status: "success",
        decoded: {
          make: "Toyota",
          model: "Camry",
          modelYear: 2022,
          transmission: { value: "Automatic", isVerified: true, source: "nhtsa" },
          fuelType: { value: "Gas", isVerified: true, source: "nhtsa" },
          seats: { value: 5, isVerified: true, source: "nhtsa" },
          doors: { value: 4, isVerified: true, source: "nhtsa" },
          bodyTypeId: 1,
        },
      });
    }
    return Promise.resolve({ listing: { listingId: 99 } });
  }),
}));

vi.mock("@/features/host/components/InstantBookToggle", () => ({
  default: ({ checked, onChange }) => (
    <input
      type="checkbox"
      data-testid="instant-book-toggle"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
    />
  ),
}));

vi.mock("lucide-react", () => ({
  UploadCloud: () => <span />,
  X: () => <span />,
  ChevronDown: () => <span />,
  BarChart3: () => <span />,
  DollarSign: () => <span />,
}));

function renderFlow() {
  return render(
    <MemoryRouter>
      <HostOnboardingFlow />
    </MemoryRouter>,
  );
}

function fillStep1() {
  fireEvent.change(screen.getByPlaceholderText(/11–17 characters/i), {
    target: { value: "1HGCM82633A004352" },
  });
}

describe("HostOnboardingFlow — VIN step", () => {
  beforeEach(() => mockNavigate.mockReset());

  it("renders VIN step headline", () => {
    renderFlow();
    expect(screen.getByText(/start with your vin/i)).toBeDefined();
  });

  it("Next stays disabled until VIN is valid", () => {
    renderFlow();
    expect(screen.getByRole("button", { name: /next/i }).disabled).toBe(true);
    fillStep1();
    expect(screen.getByRole("button", { name: /next/i }).disabled).toBe(false);
  });

  it("manual skip shows trust warning on step 2", async () => {
    renderFlow();
    fireEvent.click(screen.getByRole("button", { name: /don't have my vin/i }));
    await vi.waitFor(() =>
      expect(screen.getByText(/trust notice/i)).toBeDefined(),
    );
    expect(screen.getByText(/hidden from search/i)).toBeDefined();
  });
});
