import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const makurdi = "Makurdi Local Government Area";

async function mockSession(page: Page, role: string, canViewHr: boolean) {
  await page.route("**/version.json", route => route.fulfill({ json: { commit: "development" } }));
  await page.route("**/api/method/dtmgp.api.v1.context.get_current_user_context", route => route.fulfill({
    json: { message: {
      user: { email: "staff@example.com", full_name: "Test Officer", roles: [role] },
      allowed_lgas: [makurdi], active_lga: makurdi, can_change_lga: false,
      can_manage_users: false, can_view_hr: canViewHr, can_manage_hr: canViewHr,
      navigation: { modules: canViewHr ? [{ id: "hr", label: "Human Resources & Staff", icon: "users", to: null, children: [{ id: "hr-overview", label: "HR Overview", to: "/people", children: [] }] }] : [], global: [] },
      csrf_token: "test",
    } },
  }));
  await page.route("**/api/method/dtmgp.api.v1.overview.get_overview**", route => route.fulfill({ json: { message: {
    scope: makurdi, lga_count: 1, user_count: 1, active_user_count: 1, disabled_user_count: 0,
    unassigned_role_count: 0, can_manage_users: false, is_statewide: false, workforce: null,
  } } }));
}

test("authorized HR role receives its server-provided workspace", async ({ page }) => {
  await mockSession(page, "HR Officer", true);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Good morning, Test" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Human Resources & Staff/ })).toBeVisible();
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter(item => item.impact === "critical")).toEqual([]);
});

test("user without HR permission is redirected from a guessed HR route", async ({ page }) => {
  await mockSession(page, "Treasurer", false);
  await page.goto("/people");
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Good morning, Test" })).toBeVisible();
});

test("HR role sees the overall employee dashboard without critical accessibility violations", async ({ page }) => {
  await mockSession(page, "HR Officer", true);
  const row = (label: string, value: number) => ({ label, value });
  await page.route("**/api/method/dtmgp.api.v1.people.get_workforce_dashboard**", route => route.fulfill({ json: { message: {
    scope: { companies: 1, is_statewide: false },
    totals: { total: 8, active: 7, left: 1, verified: 4, pending_verification: 3, retiring_12m: 1, past_retirement: 0, joined_this_year: 1, average_age: 42.3 },
    breakdowns: {
      lga: [{ label: "Makurdi LGA", company: makurdi, value: 7, verified: 4 }],
      status: [row("Active", 7), row("Left", 1)], gender: [row("Female", 4), row("Male", 3)],
      grade_level: [row("GL 06", 2), row("GL 08", 3), row("GL 12", 2)], verification: [row("Verified", 4), row("Pending", 3)],
      age_band: [row("Under 25", 0), row("25 - 34", 2), row("35 - 44", 3), row("45 - 54", 2)],
      department: [row("Works", 3), row("Health", 2), row("Accounts", 2)],
      retirements_by_year: [row("2026", 1), row("2027", 0), row("2028", 2)], appointments_by_year: [row("2024", 2), row("2025", 1), row("2026", 1)],
    },
  } } }));
  await page.goto("/people/dashboard");
  await expect(page.getByRole("heading", { name: "Employee Dashboard" })).toBeVisible();
  await expect(page.getByText("Retiring in 12 months")).toBeVisible();
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter(item => item.impact === "critical")).toEqual([]);
});
