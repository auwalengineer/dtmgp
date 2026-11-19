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

test("staff directory filters send their values to the server and stay accessible", async ({ page }) => {
  await mockSession(page, "HR Officer", true);
  const employee = { name: "HR-EMP-00001", employee_name: "Amina Bello", first_name: "Amina", last_name: "Bello", company: makurdi, department: "Finance", designation: "Officer", status: "Active", date_of_joining: "2020-01-01", date_of_birth: "1990-01-01", gender: "Female", image: null, dtmgp_grade_level: "GL 08", dtmgp_verification_status: "Verified" };
  const listRequests: URLSearchParams[] = [];
  await page.route("**/api/method/dtmgp.api.v1.people.get_dashboard**", route => route.fulfill({ json: { message: { total: 1, active: 1, verified: 1, on_leave: 0, needs_attention: 0, can_manage: false } } }));
  await page.route("**/api/method/dtmgp.api.v1.people.get_form_options**", route => route.fulfill({ json: { message: { departments: ["Finance"], designations: ["Officer"], genders: ["Male", "Female"], statuses: ["Active", "Inactive", "Suspended", "Left"], verification_statuses: ["Pending", "Verified", "Review Due"], grade_levels: ["GL 07", "GL 08"] } } }));
  await page.route("**/api/method/dtmgp.api.v1.hr.list_lga_companies**", route => route.fulfill({ json: { message: [makurdi] } }));
  await page.route("**/api/method/dtmgp.api.v1.people.list_employees**", route => {
    listRequests.push(new URL(route.request().url()).searchParams);
    return route.fulfill({ json: { message: { items: [employee], total: 1, page: 1, page_size: 25 } } });
  });
  await page.goto("/people");
  await page.getByRole("combobox", { name: "Gender" }).selectOption("Female");
  await page.getByRole("combobox", { name: "Grade level" }).selectOption("GL 08");
  await expect(page.getByRole("button", { name: "Clear filters (2)" })).toBeVisible();
  await expect.poll(() => listRequests.at(-1)?.get("grade_level")).toBe("GL 08");
  expect(listRequests.at(-1)?.get("gender")).toBe("Female");
  const results = await new AxeBuilder({ page }).include(".directory-filters").analyze();
  expect(results.violations.filter(item => item.impact === "critical" || item.impact === "serious")).toEqual([]);
  await page.screenshot({ path: test.info().outputPath("directory-filters.png") });

  await page.getByRole("button", { name: "Clear filters (2)" }).click();
  await expect.poll(() => listRequests.at(-1)?.get("gender")).toBeNull();
});

test("HR reports render a filterable retirement forecast without serious accessibility violations", async ({ page }) => {
  await mockSession(page, "HR Officer", true);
  const reportRequests: URLSearchParams[] = [];
  await page.route("**/api/method/dtmgp.api.v1.people.get_dashboard**", route => route.fulfill({ json: { message: { total: 3, active: 3, verified: 1, on_leave: 0, needs_attention: 2, can_manage: false } } }));
  await page.route("**/api/method/dtmgp.api.v1.people.get_form_options**", route => route.fulfill({ json: { message: { departments: [], designations: [], genders: ["Male", "Female"], statuses: ["Active"], verification_statuses: ["Pending"], grade_levels: [] } } }));
  await page.route("**/api/method/dtmgp.api.v1.hr.list_lga_companies**", route => route.fulfill({ json: { message: [makurdi] } }));
  await page.route("**/api/method/dtmgp.api.v1.people.list_employees**", route => route.fulfill({ json: { message: { items: [], total: 0, page: 1, page_size: 25 } } }));
  await page.route("**/api/method/dtmgp.api.v1.hr.get_hr_report_options**", route => route.fulfill({ json: { message: {
    departments: [{ value: "Works - MKD", label: "Works" }], statuses: ["Active", "Suspended", "Inactive", "Left", "All"],
    group_by: [{ value: "department", label: "Department" }], dimensions: [{ value: "grade_level", label: "Grade level" }],
    leave_groups: [{ value: "leave_type", label: "Leave type" }], retirement_horizons: [12, 24, 36, 60], is_statewide: false,
  } } }));
  await page.route("**/api/method/dtmgp.api.v1.hr.get_hr_report?**", route => {
    reportRequests.push(new URL(route.request().url()).searchParams);
    return route.fulfill({ json: { message: {
      columns: [
        { key: "name", label: "Staff ID", type: "text" }, { key: "employee_name", label: "Name", type: "text" },
        { key: "department", label: "Department", type: "text" }, { key: "grade_level", label: "Grade", type: "text" },
        { key: "date_of_retirement", label: "Retirement date", type: "date" }, { key: "basis", label: "Basis", type: "text" },
        { key: "months_left", label: "Months left", type: "int" }, { key: "timing", label: "Timing", type: "text" },
      ],
      rows: [
        { name: "HR-EMP-00002", employee_name: "Tersoo Iorliam", department: "Works", grade_level: "GL 12", date_of_retirement: "2026-09-30", basis: "Age (60 years)", months_left: -2, timing: "Overdue" },
        { name: "HR-EMP-00001", employee_name: "Amina Bello", department: "Health", grade_level: "GL 08", date_of_retirement: "2027-04-12", basis: "Service (35 years)", months_left: 5, timing: "Within 12 months" },
      ],
      totals: null,
      summary: [{ label: "Overdue (still active)", value: 1, tone: "danger" }, { label: "Within 12 months", value: 1 }, { label: "Within 24 months", value: 1 }],
      note: "Overdue staff are active but past their retirement date: confirm an approved extension or process the exit.", truncated: false,
    } } });
  });
  await page.goto("/workspace/hr/hr-reports/retirement-forecast");
  await expect(page.getByRole("heading", { name: "Retirement Forecast" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Tersoo Iorliam" })).toBeVisible();
  await page.getByRole("combobox", { name: "Horizon" }).selectOption("60");
  await expect.poll(() => reportRequests.at(-1)?.get("months")).toBe("60");
  expect(reportRequests.at(-1)?.get("report")).toBe("retirement-forecast");
  const results = await new AxeBuilder({ page }).include(".hr-report").analyze();
  expect(results.violations.filter(item => item.impact === "critical" || item.impact === "serious")).toEqual([]);
  await page.screenshot({ path: test.info().outputPath("hr-reports.png"), fullPage: true });
});

test("staff profile picker searches the whole LGA on the server", async ({ page }) => {
  await mockSession(page, "HR Officer", true);
  const staff = [
    { name: "HR-EMP-00001", employee_name: "Amina Bello", designation: "Officer", status: "Active", image: null },
    { name: "HR-EMP-00002", employee_name: "Tersoo Iorliam", designation: "Accountant", status: "Active", image: null },
  ];
  const searches: (string | null)[] = [];
  await page.route("**/api/method/dtmgp.api.v1.people.get_dashboard**", route => route.fulfill({ json: { message: { total: 2, active: 2, verified: 0, on_leave: 0, needs_attention: 2, can_manage: false } } }));
  await page.route("**/api/method/dtmgp.api.v1.people.get_form_options**", route => route.fulfill({ json: { message: { departments: [], designations: [], genders: [], statuses: [], verification_statuses: [], grade_levels: [] } } }));
  await page.route("**/api/method/dtmgp.api.v1.hr.list_lga_companies**", route => route.fulfill({ json: { message: [makurdi] } }));
  await page.route("**/api/method/dtmgp.api.v1.hr.list_restricted_hr_records**", route => route.fulfill({ json: { message: [] } }));
  await page.route("**/api/method/dtmgp.api.v1.people.get_employee_profile**", route => route.fulfill({ json: { message: {
    name: "HR-EMP-00002", employee_name: "Tersoo Iorliam", image: null, company: makurdi, department: "Works", designation: "Accountant", status: "Active",
    gender: "Male", date_of_birth: "1980-01-01", date_of_joining: "2010-01-01", grade_level: "GL 10", verification_status: "Pending",
    cell_number: null, personal_email: null, emergency_contact: { person_to_be_contacted: null, relation: null, emergency_phone_number: null },
    internal_work_history: [], external_work_history: [],
    sections: [
      { label: "Personal", fields: [{ label: "Staff ID", value: "HR-EMP-00002", type: "text" }, { label: "Gender", value: "Male", type: "text" }, { label: "Date of birth", value: "1980-01-01", type: "date" }, { label: "Age", value: 46.9, type: "years" }, { label: "Qualifications", value: null, type: "text" }] },
      { label: "Service & appointment", fields: [{ label: "Department", value: "Works", type: "text" }, { label: "Grade level", value: "GL 10", type: "text" }, { label: "Step", value: 4, type: "text" }, { label: "Date of retirement", value: "2040-01-01", type: "date" }, { label: "Retirement basis", value: "Age (60 years)", type: "text" }] },
      { label: "Verification & identity", fields: [{ label: "Verification status", value: "Pending", type: "text" }, { label: "BVN", value: "•••••••5678", type: "masked" }, { label: "NIN", value: null, type: "masked" }] },
      { label: "Pay & bank", fields: [{ label: "Salary mode", value: "Bank", type: "text" }, { label: "Bank", value: "First Bank of Nigeria Limited", type: "text" }, { label: "Account number", value: "••••••6789", type: "masked" }] },
    ],
  } } }));
  await page.route("**/api/method/dtmgp.api.v1.people.list_employees**", route => {
    const term = new URL(route.request().url()).searchParams.get("search");
    searches.push(term);
    const items = term ? staff.filter(person => person.employee_name.toLowerCase().includes(term.toLowerCase())) : staff;
    return route.fulfill({ json: { message: { items, total: items.length, page: 1, page_size: 20 } } });
  });
  await page.goto("/workspace/hr/staff/staff-profiles");
  const picker = page.getByRole("combobox", { name: "Staff member" });
  await picker.fill("ters");
  await expect.poll(() => searches.at(-1)).toBe("ters");
  await expect(page.getByRole("option")).toHaveCount(1);
  const results = await new AxeBuilder({ page }).include(".employee-picker").analyze();
  expect(results.violations.filter(item => item.impact === "critical" || item.impact === "serious")).toEqual([]);
  await page.screenshot({ path: test.info().outputPath("employee-picker.png") });
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Service & appointment" })).toBeVisible();
  await expect(page.getByText("••••••6789")).toBeVisible();
  const profileResults = await new AxeBuilder({ page }).include(".profile-sections").analyze();
  expect(profileResults.violations.filter(item => item.impact === "critical" || item.impact === "serious")).toEqual([]);
  await page.screenshot({ path: test.info().outputPath("employee-profile.png"), fullPage: true });
});
