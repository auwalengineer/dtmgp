# API reference

`openapi.yaml` and `dtmgp.postman_collection.json` in this directory are generated, not
hand-written. Regenerate them after adding or changing a `@frappe.whitelist()` function
under `dtmgp/api/v1/`:

```bash
python3 dtmgp/setup/generate_api_docs.py
```

(pure static-analysis of the source tree via Python's `ast` module — no running bench or
site needed, though `pyyaml` must be importable for the `.yaml` output; without it the
script falls back to `openapi.json`.)

- **`openapi.yaml`** — every whitelisted endpoint, grouped by module, with its parameters
  and a standard set of error responses. It does not (and cannot, from static analysis
  alone) describe each endpoint's actual success response shape — see
  `../naming-and-coding-conventions.md`'s "API conventions" section for that.
- **`dtmgp.postman_collection.json`** — the same endpoint list as an importable Postman
  v2.1 collection (Bruno imports Postman collections directly, so this also covers a
  Bruno collection without maintaining two formats). Set the collection's `base_url`
  variable to your bench site and authenticate once via `/api/method/login` (or log in
  through the browser first, if your client shares its cookie jar) — every request is
  same-origin, cookie-authenticated, with no separate API-key scheme.

The generator does not infer response bodies, only the request shape (path, method,
parameters) — do not treat the `200` response schema in `openapi.yaml` as authoritative;
treat `docs/naming-and-coding-conventions.md` as the source of truth for envelope shape.
