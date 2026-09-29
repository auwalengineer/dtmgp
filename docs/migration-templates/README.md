# HR production migration templates

These header-only CSV files define the approved import shape. Populate copies in a controlled migration workspace; never commit production personal data or private file URLs.

- `employee_id` must match the ERPNext Employee identifier.
- `company` must be one of the seeded 23 LGA companies.
- Dates use ISO `YYYY-MM-DD` format.
- `classification` is `Restricted` or `Confidential`.
- `private_file_url` must resolve to a Frappe `File` with `is_private = 1` before the Staff Document can be imported.
- Run a dry-run import in staging and reconcile row counts and rejected rows before production execution.
