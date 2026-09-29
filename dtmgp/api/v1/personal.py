import frappe

from dtmgp.permissions.scope import can_view_governance, require_authenticated_user

"""Backs the global "My Tasks"/"My Approvals" workspaces (dtmgp/navigation.py's
GLOBAL_MENU) -- these are personal-scoped views, not a new domain module, so they
live here rather than under an existing domain's api/v1 file."""


@frappe.whitelist()
def get_my_tasks():
	"""Open ToDos assigned to the caller via Frappe's native assignment mechanism (the
	`_assign` field every doctype already supports) -- no new doctype, same precedent
	PRJ-001 set for reusing native ERPNext/HRMS concepts instead of duplicating them.
	Already inherently scoped to the caller (allocated_to=self), so no company/LGA
	check is needed the way a list of business records would require."""
	require_authenticated_user()
	return {"items": frappe.get_all(
		"ToDo",
		filters={"allocated_to": frappe.session.user, "status": "Open"},
		fields=["name", "description", "reference_type", "reference_name", "date", "priority"],
		order_by="date asc, priority desc",
		limit_page_length=100,
	)}


@frappe.whitelist()
def get_my_approvals():
	"""Cross-module "pending my action" is not unified across Finance/HR/Traditional/
	Governance yet -- see docs/implementation-status.md's Notifications backlog item.
	This surfaces the one real, already-built approvals inbox (Governance's
	get_approvals_inbox) rather than fabricating a wider aggregate; callers without
	governance access simply see none, since My Approvals is a personal workspace
	that should render for everyone, not error for roles outside Governance."""
	require_authenticated_user()
	if not can_view_governance():
		return {"items": [], "governance_scoped": True}
	from dtmgp.api.v1.governance import get_approvals_inbox

	return {"items": get_approvals_inbox(), "governance_scoped": True}
