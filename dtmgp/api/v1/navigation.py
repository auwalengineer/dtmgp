import frappe

from dtmgp.navigation import get_navigation as build_navigation
from dtmgp.permissions.scope import require_authenticated_user


@frappe.whitelist()
def get_navigation():
	require_authenticated_user()
	return build_navigation()
