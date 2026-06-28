import { expect, test } from "@playwright/test";

const apiURL = process.env.E2E_API_URL || "http://localhost:5000";

const SMOKE_BOOKING_START = "2099-12-01T10:00:00Z";
const SMOKE_BOOKING_END = "2099-12-04T10:00:00Z";

async function registerUser(request, prefix) {
  const email = `${prefix}-${Date.now()}@example.com`;
  const password = "E2eTest123!";
  const reg = await request.post(`${apiURL}/api/auth/register`, {
    data: { email, password, fullName: prefix },
  });
  expect(reg.ok(), await reg.text()).toBeTruthy();
  const regBody = await reg.json();
  const verifyToken = regBody.verificationToken;
  expect(verifyToken, "DEBUG=1 must return verificationToken for e2e").toBeTruthy();
  const verifyResp = await request.get(
    `${apiURL}/api/auth/verify-email?token=${encodeURIComponent(verifyToken)}`,
  );
  expect(verifyResp.ok(), await verifyResp.text()).toBeTruthy();
  return { email, password, token: regBody.token, user: regBody.user };
}

async function createSmokeListing(request, hostToken) {
  const resp = await request.post(`${apiURL}/api/listings`, {
    headers: { Authorization: `Bearer ${hostToken}` },
    data: {
      title: `E2E Smoke ${Date.now()}`,
      make: "Toyota",
      model: "Corolla",
      year: 2022,
      pricePerDay: 45.0,
      lat: 45.5017,
      lng: -73.5673,
      cityZone: "montreal",
      instantBook: true,
    },
  });
  expect(resp.ok(), await resp.text()).toBeTruthy();
  return (await resp.json()).listing.listingId;
}

test.describe("VROOM smoke", () => {
  test("API health responds", async ({ request }) => {
    const resp = await request.get(`${apiURL}/api/health`);
    expect(resp.ok()).toBeTruthy();
  });

  test("search page loads listings", async ({ page }) => {
    await page.goto("/app");
    await expect(
      page.getByRole("heading", { name: /popular locations and vehicles/i }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test("renter can create booking via API and see trip pending payment", async ({ request }) => {
    const host = await registerUser(request, "e2e-booking-host");
    const listingId = await createSmokeListing(request, host.token);
    const renter = await registerUser(request, "e2e-renter");

    const bookingResp = await request.post(`${apiURL}/api/bookings`, {
      headers: { Authorization: `Bearer ${renter.token}` },
      data: {
        listingId,
        startAt: SMOKE_BOOKING_START,
        endAt: SMOKE_BOOKING_END,
      },
    });
    expect(bookingResp.status(), await bookingResp.text()).toBe(201);
    const booking = (await bookingResp.json()).booking;
    expect(booking.status).toBe("PENDING");

    const payResp = await request.post(`${apiURL}/api/bookings/${booking.bookingId}/payments`, {
      headers: { Authorization: `Bearer ${renter.token}` },
    });
    expect(payResp.ok()).toBeTruthy();
    const paid = await payResp.json();
    expect(paid.mock).toBe(true);

    const detailResp = await request.get(`${apiURL}/api/bookings/${booking.bookingId}`, {
      headers: { Authorization: `Bearer ${renter.token}` },
    });
    const detail = (await detailResp.json()).booking;
    expect(["CONFIRMED", "PENDING_APPROVAL"]).toContain(detail.status);
  });

  test("host can open dashboard listings tab", async ({ page, request }) => {
    const host = await registerUser(request, "e2e-host");
    // /host/dashboard is gated by RequireHost (hasListings): a fresh host must own a
    // listing first, and the seeded auth user needs hasListings so the guard passes
    // on first paint (before refreshMe re-fetches /api/me).
    await createSmokeListing(request, host.token);
    await page.addInitScript(({ token, user }) => {
      localStorage.setItem("accessToken", token);
      localStorage.setItem("authUser", JSON.stringify({ ...user, hasListings: true }));
    }, { token: host.token, user: host.user });
    await page.goto("/host/dashboard");
    await expect(page.getByRole("heading", { name: /^overview$/i })).toBeVisible({
      timeout: 15_000,
    });
    await page.getByRole("button", { name: /^listings$/i }).click();
    await expect(page.getByRole("heading", { name: /manage listings/i })).toBeVisible({
      timeout: 15_000,
    });
  });
});
