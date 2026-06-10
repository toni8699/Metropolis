import { expect, test } from "@playwright/test";

const apiURL = process.env.E2E_API_URL || "http://localhost:5000";

async function registerUser(request, prefix) {
  const email = `${prefix}-${Date.now()}@e2e.test`;
  const password = "E2eTest123!";
  const resp = await request.post(`${apiURL}/api/auth/register`, {
    data: { email, password, fullName: prefix },
  });
  expect(resp.ok()).toBeTruthy();
  const body = await resp.json();
  return { email, password, token: body.token, user: body.user };
}

test.describe("Metropolis smoke", () => {
  test("API health responds", async ({ request }) => {
    const resp = await request.get(`${apiURL}/api/health`);
    expect(resp.ok()).toBeTruthy();
  });

  test("search page loads listings", async ({ page }) => {
    await page.goto("/app/browse");
    await expect(page.getByRole("heading", { name: /browse|search|cars/i }).first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test("renter can create booking via API and see trip pending payment", async ({ request }) => {
    const renter = await registerUser(request, "e2e-renter");
    const listingsResp = await request.get(`${apiURL}/api/market/listings`);
    expect(listingsResp.ok()).toBeTruthy();
    const listings = (await listingsResp.json()).listings || [];
    test.skip(listings.length === 0, "No listings seeded for E2E");
    const listingId = listings[0].listingId;

    const bookingResp = await request.post(`${apiURL}/api/bookings`, {
      headers: { Authorization: `Bearer ${renter.token}` },
      data: {
        listingId,
        startAt: "2099-08-01T10:00:00Z",
        endAt: "2099-08-04T10:00:00Z",
      },
    });
    expect(bookingResp.status()).toBe(201);
    const booking = (await bookingResp.json()).booking;
    expect(booking.status).toBe("PENDING");

    const payResp = await request.post(`${apiURL}/api/bookings/${booking.bookingId}/payment-intent`, {
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
    await page.addInitScript((token) => {
      localStorage.setItem("accessToken", token);
    }, host.token);
    await page.goto("/app/host");
    await expect(page.getByText(/host dashboard|manage listings/i).first()).toBeVisible({
      timeout: 15_000,
    });
  });
});
