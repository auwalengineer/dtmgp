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
