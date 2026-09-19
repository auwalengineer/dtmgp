app_name = "dtmgp"
app_title = "dtmgp"
app_publisher = "Auwal Isiaku	"
app_description = "Local Government Digital Transformation, Management and Governance Platform"
app_email = "engr.auwal@live.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext", "hrms"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "dtmgp",
# 		"logo": "/assets/dtmgp/logo.png",
# 		"title": "dtmgp",
# 		"route": "/dtmgp",
# 		"has_permission": "dtmgp.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/dtmgp/css/dtmgp.css"
app_include_js = "/assets/dtmgp/js/dtmgp.js"

# include js, css files in header of web template
web_include_css = [
	"/assets/dtmgp/css/dtmgp.css",
	"/assets/dtmgp/css/login.css",
]

website_context = {
	"splash_image": "/assets/dtmgp/images/benue-govt-logo.jpeg",
}

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dtmgp/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dtmgp/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "dtmgp.utils.jinja_methods",
# 	"filters": "dtmgp.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dtmgp.install.before_install"
after_install = "dtmgp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dtmgp.uninstall.before_uninstall"
# after_uninstall = "dtmgp.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dtmgp.utils.before_app_install"
# after_app_install = "dtmgp.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dtmgp.utils.before_app_uninstall"
# after_app_uninstall = "dtmgp.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dtmgp.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["dtmgp.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
permission_query_conditions = {
	"User": "dtmgp.permissions.user.get_permission_query_conditions",
	"DTMGP Audit Event": "dtmgp.permissions.audit_event.get_permission_query_conditions",
	"DTMGP Approval Limit": "dtmgp.permissions.finance.approval_limit_query",
	"DTMGP Revenue Head": "dtmgp.permissions.finance.revenue_head_query",
	"DTMGP Revenue Assessment": "dtmgp.permissions.finance.revenue_assessment_query",
	"DTMGP Revenue Receipt": "dtmgp.permissions.finance.revenue_receipt_query",
	"DTMGP Procurement Plan": "dtmgp.permissions.finance.procurement_plan_query",
	"DTMGP Procurement Case": "dtmgp.permissions.finance.procurement_case_query",
	"DTMGP Payment Request": "dtmgp.permissions.finance.payment_request_query",
	"DTMGP Audit Query": "dtmgp.permissions.finance.audit_query_query",
	"DTMGP Staff Verification Exercise": "dtmgp.permissions.hr.verification_exercise_query",
	"DTMGP Staff Verification Record": "dtmgp.permissions.hr.verification_record_query",
	"DTMGP Correspondence": "dtmgp.permissions.governance.correspondence_query",
	# Employee Transfer has two Company-Link fields (`company`, `new_company`); its
	# custom query condition ORs across both so the destination LGA can see an
	# inbound transfer. See dtmgp.setup.security.seed_employee_transfer_property_setters
	# for why `new_company` is exempted from Frappe's automatic per-field filtering.
	"Employee Transfer": "dtmgp.permissions.hr.employee_transfer_query",
	# Project/Task back the Employee Separation exit-clearance checklist; Task has no
	# company field of its own, so it's scoped through its Project.
	"Project": "dtmgp.permissions.hr.project_query",
	"Task": "dtmgp.permissions.hr.task_query",
	"Shift Assignment": "dtmgp.permissions.hr.shift_assignment_query",
}
#
has_permission = {
	"User": "dtmgp.permissions.user.has_permission",
	"DTMGP Audit Event": "dtmgp.permissions.audit_event.has_permission",
	"DTMGP Approval Limit": "dtmgp.permissions.finance.has_permission",
	"DTMGP Revenue Head": "dtmgp.permissions.finance.has_permission",
	"DTMGP Revenue Assessment": "dtmgp.permissions.finance.has_permission",
	"DTMGP Revenue Receipt": "dtmgp.permissions.finance.has_permission",
	"DTMGP Procurement Plan": "dtmgp.permissions.finance.has_permission",
	"DTMGP Procurement Case": "dtmgp.permissions.finance.has_permission",
	"DTMGP Payment Request": "dtmgp.permissions.finance.has_permission",
	"DTMGP Audit Query": "dtmgp.permissions.finance.has_permission",
	"DTMGP Staff Verification Exercise": "dtmgp.permissions.hr.has_permission",
	"DTMGP Staff Verification Record": "dtmgp.permissions.hr.has_permission",
	"DTMGP Correspondence": "dtmgp.permissions.governance.has_permission",
	"Employee Transfer": "dtmgp.permissions.hr.employee_transfer_has_permission",
	"Project": "dtmgp.permissions.hr.has_permission",
	"Task": "dtmgp.permissions.hr.task_has_permission",
	"Shift Assignment": "dtmgp.permissions.hr.has_permission",
}

doc_events = {
	"User": {
		"validate": "dtmgp.permissions.user_events.validate_user_scope",
		"on_update": ["dtmgp.permissions.user_events.sync_user_lga_permission", "dtmgp.audit.audit_user_change"],
		"after_insert": ["dtmgp.permissions.user_events.sync_user_lga_permission", "dtmgp.audit.audit_user_change"],
	},
	"User Permission": {
		"after_insert": "dtmgp.audit.audit_user_permission",
		"on_update": "dtmgp.audit.audit_user_permission",
		"on_trash": "dtmgp.audit.audit_user_permission",
	},
	"DTMGP Approval Limit": {"on_update": "dtmgp.audit.audit_finance_change", "after_insert": "dtmgp.audit.audit_finance_change", "on_trash": "dtmgp.audit.audit_finance_change"},
	"DTMGP Revenue Head": {"on_update": "dtmgp.audit.audit_finance_change", "after_insert": "dtmgp.audit.audit_finance_change", "on_trash": "dtmgp.audit.audit_finance_change"},
	"DTMGP Revenue Assessment": {"on_update": "dtmgp.audit.audit_finance_change", "after_insert": "dtmgp.audit.audit_finance_change", "on_submit": "dtmgp.audit.audit_finance_change", "on_cancel": "dtmgp.audit.audit_finance_change"},
	"DTMGP Revenue Receipt": {"on_update": "dtmgp.audit.audit_finance_change", "after_insert": "dtmgp.audit.audit_finance_change", "on_submit": "dtmgp.audit.audit_finance_change", "on_cancel": "dtmgp.audit.audit_finance_change"},
	"DTMGP Procurement Plan": {"on_update": "dtmgp.audit.audit_finance_change", "after_insert": "dtmgp.audit.audit_finance_change"},
	"DTMGP Procurement Case": {"on_update": "dtmgp.audit.audit_finance_change", "after_insert": "dtmgp.audit.audit_finance_change"},
	"DTMGP Payment Request": {"on_update": "dtmgp.audit.audit_finance_change", "after_insert": "dtmgp.audit.audit_finance_change"},
	"DTMGP Audit Query": {"on_update": "dtmgp.audit.audit_finance_change", "after_insert": "dtmgp.audit.audit_finance_change"},
	"DTMGP Staff Verification Exercise": {"on_update": "dtmgp.audit.audit_hr_change", "after_insert": "dtmgp.audit.audit_hr_change"},
	"DTMGP Staff Verification Record": {"on_update": "dtmgp.audit.audit_hr_change", "after_insert": "dtmgp.audit.audit_hr_change"},
	"DTMGP Correspondence": {"on_update": "dtmgp.audit.audit_governance_change", "after_insert": "dtmgp.audit.audit_governance_change", "on_trash": "dtmgp.audit.audit_governance_change"},
	"Staffing Plan": {"on_submit": "dtmgp.audit.audit_hr_change", "on_cancel": "dtmgp.audit.audit_hr_change"},
	"Employee Transfer": {"on_submit": "dtmgp.audit.audit_hr_change", "on_cancel": "dtmgp.audit.audit_hr_change"},
	"Employee Promotion": {"on_submit": "dtmgp.audit.audit_hr_change", "on_cancel": "dtmgp.audit.audit_hr_change"},
	"Employee Separation": {"on_submit": "dtmgp.audit.audit_hr_change", "on_cancel": "dtmgp.audit.audit_hr_change"},
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dtmgp.tasks.all"
# 	],
# 	"daily": [
# 		"dtmgp.tasks.daily"
# 	],
# 	"hourly": [
# 		"dtmgp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dtmgp.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dtmgp.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "dtmgp.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dtmgp.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dtmgp.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dtmgp.utils.before_request"]
# after_request = ["dtmgp.utils.after_request"]

# Job Events
# ----------
# before_job = ["dtmgp.utils.before_job"]
# after_job = ["dtmgp.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dtmgp.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
