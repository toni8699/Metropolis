import { describe, expect, it } from "vitest";
import { avatarInitials, avatarLabel } from "@/shared/lib/avatar";

describe("avatarInitials", () => {
  it("uses two initials from full name", () => {
    expect(avatarInitials("Jane Doe")).toBe("JD");
  });

  it("caps single-word names at two characters", () => {
    expect(avatarInitials("Jane")).toBe("JA");
  });

  it("falls back to email prefix when name missing", () => {
    expect(avatarInitials("", "jane@example.com")).toBe("JA");
  });
});

describe("avatarLabel", () => {
  it("prefers full name over email", () => {
    expect(avatarLabel({ fullName: "Jane Doe", email: "jane@example.com" })).toBe("Jane Doe");
  });

  it("uses email when full name missing", () => {
    expect(avatarLabel({ email: "jane@example.com" })).toBe("jane@example.com");
  });
});
