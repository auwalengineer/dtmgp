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
  const lga = (name: string, active: number, femalePct: number) => ({
    company: `${name} Local Government Area`, label: `${name} LGA`, total: active, active, left: 0, verified: Math.floor(active / 2),
    pending_verification: active - Math.floor(active / 2), retiring_12m: 1, past_retirement: 0, joined_this_year: 0,
    average_age: active ? 42 : null, average_service: active ? 11 : null, male: active - Math.round(active * femalePct / 100), female: Math.round(active * femalePct / 100),
    share_pct: 0, verified_pct: 50, female_pct: femalePct, management_pct: 10, bvn_pct: 80, nin_pct: 70, photo_pct: 20, bank_pct: 90,
    phone_pct: 50, first_appointment_pct: 60, grade_bands: { "Junior (GL 01-06)": 2, "Senior (GL 07-12)": active - 2, "Management (GL 13-17)": 0 },
  });
  await page.route("**/api/method/dtmgp.api.v1.people.get_workforce_dashboard**", route => route.fulfill({ json: { message: {
    scope: { companies: 3, is_statewide: true },
    totals: { total: 15, active: 15, left: 0, suspended_or_inactive: 0, verified: 7, pending_verification: 8, male: 8, female: 7, retiring_12m: 3, retiring_5y: 5,
      past_retirement: 0, joined_this_year: 1, average_age: 42.3, average_service: 11, completeness: { bvn: 80, nin: 70, photo: 20, bank: 90, phone: 50, first_appointment: 60 } },
    breakdowns: {
      lga: [{ label: "Makurdi LGA", company: makurdi, value: 7, verified: 4 }],
      status: [row("Active", 15)], gender: [row("Male", 8), row("Female", 7)],
      grade_level: [row("GL 06", 2), row("GL 08", 3), row("GL 12", 2)], grade_band: [row("Junior (GL 01-06)", 6), row("Senior (GL 07-12)", 9)],
      verification: [row("Verified", 7), row("Pending", 8)], age_band: [row("25 - 34", 5), row("35 - 44", 6), row("45 - 54", 4)],
      service_band: [row("5 - 9 years", 7), row("10 - 19 years", 8)], department: [row("Works", 8), row("Health", 7)],
      designation: [row("Clerk", 9)], rank: [row("Officer I", 5)], salary_mode: [row("Bank", 15)],
      data_completeness: [{ label: "BVN", value: 80, count: 12 }, { label: "NIN", value: 70, count: 10 }],
      retirements_by_year: [row("2026", 1), row("2027", 0), row("2028", 2)], appointments_by_year: [row("2024", 2), row("2025", 1), row("2026", 1)],
    },
    lga_comparison: [lga("Makurdi", 7, 57), lga("Gboko", 5, 40), lga("Otukpo", 3, 33)],
    comparison_metrics: [{ key: "active", label: "Active staff", unit: "count" }, { key: "female_pct", label: "Female", unit: "pct" }],
  } } }));
  await page.goto("/people/dashboard");
  await expect(page.getByRole("heading", { name: "Employee Dashboard" })).toBeVisible();
  await expect(page.getByText("Retiring in 12 months")).toBeVisible();
  await expect(page.getByRole("heading", { name: "LGA comparison", exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toContainText("Otukpo LGA");
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter(item => item.impact === "critical")).toEqual([]);
});
