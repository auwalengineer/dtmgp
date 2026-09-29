from uuid import uuid4

import frappe
from frappe.sessions import Session, get_expired_sessions, get_expired_threshold, get_expiry_in_seconds, get_sessions_to_clear
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, cint, now

from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

"""P0 FND-008: automated expired-session, disabled-user and concurrent-session
coverage, exercising the exact Frappe session-lifecycle functions a real request
goes through (frappe/sessions.py, frappe/auth.py) rather than simulating them --
dtmgp defines no session/auth hooks of its own (dtmgp/hooks.py has none), so this
proves the stock behavior actually holds for a real dtmgp user/role/site config.

These tests deliberately avoid every code path that calls frappe.db.commit()
internally (Session.start(), delete_session(), clear_sessions(), LoginManager.login/
login_as) -- FrappeTestCase only rolls back once, at class teardown (see
frappe/tests/utils.py's addClassCleanup(_rollback_db)), not per test method, so an
explicit commit anywhere would permanently write test fixtures (including the User
records created in setUp) into the site's real database. Session rows are inserted
directly via raw SQL (the same pattern dtmgp/permissions/test_administration.py's
_insert_session already uses) and validated against the real decision functions
(get_expired_sessions, get_expired_threshold, get_sessions_to_clear,
Session.validate_user) instead of performing an end-to-end login/logout."""


class TestSessionLifecycle(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.user = self._make_user("Treasurer", self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	# --------------------------------------------------------------------- Expiry

	def test_expired_sessions_are_identified_and_excluded_from_valid_data(self):
		"""Mirrors the exact functions Session.get_session_data_from_db()/
		clear_expired_sessions() use on every request and on the scheduler's cleanup
		task, for a real dtmgp session row rather than Frappe core's own Administrator
		fixture."""
		expiry_in = get_expiry_in_seconds()
		fresh_sid = self._insert_session(self.user.name)
		stale_sid = self._insert_session(self.user.name, lastupdate=add_to_date(now(), seconds=-(expiry_in * 1.01), as_string=True))

		expired = get_expired_sessions()
		self.assertIn(stale_sid, expired)
		self.assertNotIn(fresh_sid, expired)

		# The precise WHERE clause Session.get_session_data_from_db() applies to decide
		# whether a session row is still resumable. "Sessions" is a raw table with no
		# DocType meta, so it's queried directly rather than via frappe.get_all.
		threshold = get_expired_threshold()
		self.assertFalse(self._session_is_resumable(stale_sid, threshold))
		self.assertTrue(self._session_is_resumable(fresh_sid, threshold))

	# --------------------------------------------------------------- Disabled user

	def test_disabled_user_session_is_rejected_on_the_next_request(self):
		"""Session.resume() calls validate_user() on every request that resumes an
		existing session (not just at login) -- this is what makes disabling a User
		mid-session take effect immediately, without waiting for the session to expire
		or the user to log out. Session.__new__ bypasses __init__'s dependency on a
		live frappe.request (cookies/form_dict), which validate_user() doesn't need."""
		self._insert_session(self.user.name)
		frappe.db.set_value("User", self.user.name, "enabled", 0)
		frappe.clear_cache(user=self.user.name)

		session = Session.__new__(Session)
		session.user = self.user.name
		with self.assertRaises(frappe.ValidationError):
			session.validate_user()

		frappe.db.set_value("User", self.user.name, "enabled", 1)
		frappe.clear_cache(user=self.user.name)
		session.validate_user()  # re-enabling the account is accepted again, no exception

	# ----------------------------------------------------------------- Concurrent

	def test_concurrent_sessions_are_allowed_by_default(self):
		"""Default site configuration ("Allow only one session per user" off) is the
		state a fresh dtmgp install/seed leaves System Settings in -- LoginManager.
		clear_active_sessions() short-circuits before ever calling clear_sessions(),
		so multiple simultaneous logins for one user are kept."""
		self.assertFalse(cint(frappe.db.get_system_setting("deny_multiple_sessions")))
		first_sid = self._insert_session(self.user.name)
		second_sid = self._insert_session(self.user.name)
		self.assertTrue(self._session_exists(first_sid))
		self.assertTrue(self._session_exists(second_sid))

	def test_deny_multiple_sessions_flags_every_other_session_for_eviction(self):
		"""With "Allow only one session per user" enabled, a fresh login's
		LoginManager.clear_active_sessions() calls clear_sessions(user, keep_current=
		True), which resolves the sids to evict via get_sessions_to_clear -- proves
		that resolution picks up both fixture sessions for this user without actually
		invoking clear_sessions/delete_session, which call frappe.db.commit() and so
		must never run inside a test (see module docstring)."""
		first_sid = self._insert_session(self.user.name)
		second_sid = self._insert_session(self.user.name)

		frappe.db.set_single_value("System Settings", "deny_multiple_sessions", 1)
		frappe.clear_cache()
		self.addCleanup(self._reset_deny_multiple_sessions)
		self.assertTrue(cint(frappe.db.get_system_setting("deny_multiple_sessions")))

		to_clear = get_sessions_to_clear(self.user.name, keep_current=False, force=True)
		self.assertIn(first_sid, to_clear)
		self.assertIn(second_sid, to_clear)

	def _reset_deny_multiple_sessions(self):
		frappe.db.set_single_value("System Settings", "deny_multiple_sessions", 0)
		frappe.clear_cache()

	# ----------------------------------------------------------------------- fixtures

	def _session_exists(self, sid):
		return bool(frappe.db.sql("select 1 from `tabSessions` where sid=%s", sid))

	def _session_is_resumable(self, sid, threshold):
		return bool(frappe.db.sql("select 1 from `tabSessions` where sid=%s and lastupdate > %s", (sid, threshold)))

	def _insert_session(self, user, lastupdate=None):
		sid = f"session-lifecycle-{uuid4().hex}"
		frappe.db.sql(
			"insert into `tabSessions` (`user`, `sid`, `sessiondata`, `ipaddress`, `lastupdate`, `status`) "
			"values (%s, %s, %s, %s, %s, 'Active')",
			(user, sid, "{}", "127.0.0.1", lastupdate or now()),
		)
		return sid

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": f"session-iso-{uuid4().hex}@example.com",
				"first_name": "Session Isolation",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()
