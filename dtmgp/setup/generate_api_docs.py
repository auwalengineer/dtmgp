"""Generates docs/api/openapi.yaml and docs/api/dtmgp.postman_collection.json by
introspecting every @frappe.whitelist() function under dtmgp/api/v1/*.py, so the
reference stays honest by construction instead of hand-maintained and drifting out of
sync with the actual endpoints. Not part of install/migrate -- regenerate after adding
or changing an API function:

	python3 dtmgp/setup/generate_api_docs.py

(pure `ast` introspection of the source tree -- no running site/bench needed). See
docs/naming-and-coding-conventions.md's "API conventions" section for the response-
envelope and error-code conventions this reflects; this script does not (and cannot,
from static analysis alone) infer each function's actual return shape -- that section
is the source of truth for what a caller should expect back."""

import ast
import json
import os

APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API_DIR = os.path.join(APP_ROOT, "dtmgp", "api", "v1")
OUT_DIR = os.path.join(APP_ROOT, "docs", "api")
SKIP_FILES = {"__init__.py"}


def _is_whitelist_decorator(node):
	target = node.func if isinstance(node, ast.Call) else node
	if isinstance(target, ast.Attribute):
		return target.attr == "whitelist"
	if isinstance(target, ast.Name):
		return target.id == "whitelist"
	return False


def _decorator_methods(node):
	if not isinstance(node, ast.Call):
		return ["GET"]
	for kw in node.keywords:
		if kw.arg == "methods" and isinstance(kw.value, ast.List):
			values = [el.value for el in kw.value.elts if isinstance(el, ast.Constant)]
			if values:
				return values
	return ["GET"]


def _params(func_def):
	args = func_def.args
	positional = args.args
	defaults = args.defaults
	num_required = len(positional) - len(defaults)
	params = []
	for index, arg in enumerate(positional):
		has_default = index >= num_required
		default_node = defaults[index - num_required] if has_default else None
		default_value = default_node.value if isinstance(default_node, ast.Constant) else (None if has_default else None)
		params.append({"name": arg.arg, "required": not has_default, "default": default_value})
	return params


def _collect_functions():
	"""Yields (module_name, function_name, methods, params, summary) for every
	top-level @frappe.whitelist()-decorated function in dtmgp/api/v1/*.py, skipping
	private helpers (leading underscore) and test files."""
	for filename in sorted(os.listdir(API_DIR)):
		if not filename.endswith(".py") or filename in SKIP_FILES or filename.startswith("test_"):
			continue
		module_name = filename[: -len(".py")]
		with open(os.path.join(API_DIR, filename)) as handle:
			tree = ast.parse(handle.read(), filename=filename)
		for node in tree.body:
			if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
				continue
			whitelist_decorator = next((d for d in node.decorator_list if _is_whitelist_decorator(d)), None)
			if whitelist_decorator is None:
				continue
			methods = _decorator_methods(whitelist_decorator)
			docstring = ast.get_docstring(node) or ""
			summary = docstring.strip().split("\n", 1)[0] if docstring else f"{node.name} ({module_name})"
			yield module_name, node.name, methods, _params(node), summary


def _param_schema(param):
	schema = {"type": "string"}
	if param["default"] is not None:
		if isinstance(param["default"], bool):
			schema = {"type": "boolean", "default": param["default"]}
		elif isinstance(param["default"], (int, float)):
			schema = {"type": "number", "default": param["default"]}
		else:
			schema["default"] = param["default"]
	return schema


ERROR_RESPONSES = {
	"401": {"description": "AuthenticationError -- no session (Guest) or the session's user has been disabled (frappe.ValidationError, HTTP 417, is thrown instead for an already-established session's user being disabled mid-session -- see docs/implementation-status.md's FND-008 row)."},
	"403": {"description": "PermissionError -- authenticated, but the caller's role or LGA scope does not permit this request. Every scope/role/company-boundary violation in dtmgp uses this class; see docs/naming-and-coding-conventions.md's API conventions section."},
	"417": {"description": "ValidationError (Frappe's default for a bare frappe.throw(message)) -- a business-rule violation, e.g. an invalid status transition or a required cross-referenced field."},
}


def _build_openapi(functions):
	paths = {}
	for module_name, func_name, methods, params, summary in functions:
		path = f"/api/method/dtmgp.api.v1.{module_name}.{func_name}"
		operations = {}
		for method in methods:
			operation = {
				"tags": [module_name],
				"summary": summary,
				"operationId": f"{module_name}.{func_name}",
				"responses": {
					"200": {
						"description": "Success. Response body is Frappe's standard {\"message\": <result>} envelope; see docs/naming-and-coding-conventions.md's API conventions section for the shape of <result>.",
						"content": {"application/json": {"schema": {"type": "object", "properties": {"message": {}}}}},
					},
					**ERROR_RESPONSES,
				},
			}
			if method == "GET":
				operation["parameters"] = [
					{"name": p["name"], "in": "query", "required": p["required"], "schema": _param_schema(p)}
					for p in params
				]
			else:
				operation["requestBody"] = {
					"required": bool(params),
					"content": {"application/json": {"schema": {
						"type": "object",
						"properties": {p["name"]: _param_schema(p) for p in params},
						"required": [p["name"] for p in params if p["required"]],
					}}},
				}
			operations[method.lower()] = operation
		paths[path] = operations
	return {
		"openapi": "3.0.3",
		"info": {
			"title": "LG-DTMGP API",
			"version": "v1",
			"description": (
				"Auto-generated from dtmgp/api/v1/*.py's @frappe.whitelist() functions by "
				"dtmgp/setup/generate_api_docs.py -- do not hand-edit this file, regenerate it "
				"instead. Every request is same-origin, cookie-authenticated (Frappe session "
				"cookie) with an X-Frappe-CSRF-Token header on writes; there is no separate "
				"API-key auth scheme for this application. See "
				"docs/naming-and-coding-conventions.md's \"API conventions\" section for the "
				"response-envelope, pagination and error conventions this reflects."
			),
		},
		"servers": [{"url": "/", "description": "Same-origin -- the Vue app and this API are served from the same Frappe site."}],
		"paths": dict(sorted(paths.items())),
	}


def _build_postman(functions):
	by_module = {}
	for module_name, func_name, methods, params, summary in functions:
		by_module.setdefault(module_name, []).append((func_name, methods, params, summary))

	folders = []
	for module_name in sorted(by_module):
		items = []
		for func_name, methods, params, summary in sorted(by_module[module_name]):
			method = methods[0]
			path = f"/api/method/dtmgp.api.v1.{module_name}.{func_name}"
			request = {
				"name": func_name,
				"request": {
					"method": method,
					"header": [{"key": "Accept", "value": "application/json"}] + (
						[{"key": "X-Frappe-CSRF-Token", "value": "{{csrf_token}}"}] if method != "GET" else []
					),
					"url": {
						"raw": "{{base_url}}" + path + ("?" + "&".join(f"{p['name']}=" for p in params) if method == "GET" and params else ""),
						"host": ["{{base_url}}"],
						"path": path.strip("/").split("/"),
						"query": [{"key": p["name"], "value": "", "disabled": not p["required"]} for p in params] if method == "GET" else [],
					},
					"description": summary,
				},
			}
			if method != "GET" and params:
				request["request"]["body"] = {
					"mode": "raw",
					"raw": json.dumps({p["name"]: p["default"] if p["default"] is not None else "" for p in params}, indent=2),
					"options": {"raw": {"language": "json"}},
				}
			items.append(request)
		folders.append({"name": module_name, "item": items})

	return {
		"info": {
			"name": "LG-DTMGP API",
			"description": "Auto-generated by dtmgp/setup/generate_api_docs.py. Set the {{base_url}} (e.g. http://blga.local:8000) and {{csrf_token}} collection variables; both require an authenticated same-origin session cookie, which Postman/Bruno's cookie jar handles automatically once you've logged in once against the same base_url in a browser step, or via a prior /api/method/login request in this collection.",
			"schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
		},
		"variable": [
			{"key": "base_url", "value": "http://blga.local:8000"},
			{"key": "csrf_token", "value": ""},
		],
		"item": folders,
	}


def generate():
	functions = list(_collect_functions())
	os.makedirs(OUT_DIR, exist_ok=True)

	openapi = _build_openapi(functions)
	postman = _build_postman(functions)

	try:
		import yaml

		with open(os.path.join(OUT_DIR, "openapi.yaml"), "w") as handle:
			yaml.safe_dump(openapi, handle, sort_keys=False, allow_unicode=True)
	except ImportError:
		with open(os.path.join(OUT_DIR, "openapi.json"), "w") as handle:
			json.dump(openapi, handle, indent=2)

	with open(os.path.join(OUT_DIR, "dtmgp.postman_collection.json"), "w") as handle:
		json.dump(postman, handle, indent=2)

	print(f"Documented {len(functions)} endpoints across {len({m for m, *_ in functions})} modules.")


if __name__ == "__main__":
	generate()
