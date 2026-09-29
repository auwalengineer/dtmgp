type FrappeResponse<T> = { message: T };
let csrfToken = "";
export function setCsrfToken(token: string) { csrfToken = token; }
export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, { credentials: "include", ...options, headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...(csrfToken ? { "X-Frappe-CSRF-Token": csrfToken } : {}), ...options.headers } });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.exception || payload.message || "Request failed");
  return (payload as FrappeResponse<T>).message;
}
export async function uploadFile(file: File, params: { doctype?: string; docname?: string; fieldname?: string; isPrivate?: boolean }): Promise<{ file_url: string }> {
  const body = new FormData();
  body.append("file", file);
  if (params.doctype) body.append("doctype", params.doctype);
  if (params.docname) body.append("docname", params.docname);
  if (params.fieldname) body.append("fieldname", params.fieldname);
  body.append("is_private", params.isPrivate ? "1" : "0");
  const response = await fetch("/api/method/upload_file", { method: "POST", credentials: "include", headers: csrfToken ? { "X-Frappe-CSRF-Token": csrfToken } : {}, body });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.exception || payload.message || "Upload failed");
  return payload.message;
}
export async function login(username: string, password: string) {
  const response = await fetch("/api/method/login", { method: "POST", credentials: "include", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ usr: username, pwd: password }) });
  if (!response.ok) throw new Error("Invalid email or password");
}
