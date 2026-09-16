from collections import Counter

import frappe

from dtmgp.permissions.scope import get_requested_companies, get_scoped_user_names, is_state_user, require_user_admin
from dtmgp.setup.security import PLATFORM_ROLES


@frappe.whitelist()
def get_dashboard(company=None):
	require_user_admin()
	companies = get_requested_companies(company)
	user_names = get_scoped_user_names(companies=companies)
	users = _get_users(user_names)
	role_counts = Counter()
	for user in users:
		role_counts.update(role for role in frappe.get_roles(user.name) if role in PLATFORM_ROLES)

	return {
		"scope": "Statewide" if is_state_user() and not company else (companies[0] if companies else "No LGA assigned"),
		"lga_count": len(companies),
		"user_count": len(users),
		"active_user_count": sum(1 for user in users if user.enabled),
		"disabled_user_count": sum(1 for user in users if not user.enabled),
		"roles": [{"role": role, "count": count} for role, count in role_counts.most_common()],
		"recent_users": [
			{
				"name": user.name,
				"full_name": user.full_name,
				"enabled": user.enabled,
				"last_active": user.last_active,
			}
			for user in users[:5]
		],
	}


def _get_users(user_names):
	if not user_names:
		return []
	return frappe.get_all(
		"User",
		filters={"name": ["in", user_names], "user_type": "System User"},
		fields=["name", "full_name", "enabled", "last_active", "creation"],
		order_by="creation desc",
	)
