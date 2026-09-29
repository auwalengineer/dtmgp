export interface PrintableReport {
  title: string;
  columns: string[];
  rows: unknown[][];
  lga?: string;
  filters?: Record<string, string | number | null | undefined>;
}

function escapeHtml(value: unknown) {
  return String(value ?? "").replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[character] || character);
}

export function reportOrientation(report: Pick<PrintableReport, "columns" | "rows">) {
  const sample = report.rows.slice(0, 25);
  const contentWidth = report.columns.reduce((total, heading, index) => {
    const longest = Math.max(heading.length, ...sample.map(row => String(row[index] ?? "").length));
    return total + Math.min(longest, 40);
  }, 0);
  return report.columns.length >= 5 || contentWidth > 95 ? "landscape" : "portrait";
}

export function printReportDocument(report: PrintableReport) {
  const popup = window.open("", "_blank", "width=1100,height=800");
  if (!popup) throw new Error("The print window was blocked. Allow pop-ups and try again.");
  popup.opener = null;
  const orientation = reportOrientation(report);
  const generated = new Intl.DateTimeFormat("en-NG", { dateStyle: "long", timeStyle: "short", timeZone: "Africa/Lagos" }).format(new Date());
  const filters = Object.entries(report.filters || {}).filter(([, value]) => value !== undefined && value !== null && value !== "");
  const filterMarkup = filters.length ? `<section class="filters"><strong>Filters used</strong>${filters.map(([label, value]) => `<span><b>${escapeHtml(label)}:</b> ${escapeHtml(value)}</span>`).join("")}</section>` : "";
  const emptyRow = `<tr><td colspan="${report.columns.length}" class="empty">No records matched this report.</td></tr>`;
  const bodyRows = report.rows.length ? report.rows.map(row => `<tr>${report.columns.map((_column, index) => `<td>${escapeHtml(row[index])}</td>`).join("")}</tr>`).join("") : emptyRow;
  popup.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(report.title)}</title><style>
    @page { size: A4 ${orientation}; margin: 16mm 13mm 18mm; }
    * { box-sizing: border-box; } body { margin: 0; color: #17251f; font: 10pt Arial, sans-serif; }
    header { display: grid; grid-template-columns: 66px 1fr 66px; align-items: center; padding-bottom: 12px; border-bottom: 3px solid #087443; text-align: center; }
    header img { width: 58px; height: 58px; object-fit: contain; } header p, header h1, header h2 { margin: 0; }
    header h1 { font-size: 15pt; text-transform: uppercase; } header h2 { margin-top: 4px; font-size: 12pt; font-weight: 600; } header p { margin-top: 3px; font-size: 9pt; }
    .meta { display: flex; justify-content: space-between; gap: 16px; margin: 12px 0 8px; font-size: 8.5pt; }
    .filters { display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 8px 0 12px; padding: 8px 10px; border: 1px solid #cad6cf; background: #f4f7f5; }
    .filters strong { width: 100%; font-size: 8pt; text-transform: uppercase; } table { width: 100%; border-collapse: collapse; table-layout: auto; }
    thead { display: table-header-group; } th { background: #e8f1ec; color: #143d2a; font-weight: 700; text-align: left; }
    th, td { padding: 6px 7px; border: 1px solid #aebdb5; vertical-align: top; overflow-wrap: anywhere; } tbody tr:nth-child(even) { background: #f8faf9; }
    tr { break-inside: avoid; } .empty { padding: 24px; text-align: center; color: #66736c; }
    footer { position: fixed; right: 0; bottom: -10mm; left: 0; display: flex; justify-content: space-between; border-top: 1px solid #aebdb5; padding-top: 4px; color: #66736c; font-size: 7.5pt; }
    footer .page::after { content: "Page " counter(page) " of " counter(pages); }
  </style></head><body>
    <header><img src="${escapeHtml(window.location.origin)}/benue-govt-logo.jpeg" alt="Benue State Government emblem"><div><h1>Benue State Local Government Administration</h1><h2>${escapeHtml(report.title)}</h2><p>${escapeHtml(report.lga || "Statewide")} &bull; ${orientation === "landscape" ? "Landscape" : "Portrait"}</p></div><div></div></header>
    <section class="meta"><span><strong>Generated:</strong> ${escapeHtml(generated)} (WAT)</span><span><strong>Records:</strong> ${report.rows.length}</span></section>
    ${filterMarkup}<table><thead><tr>${report.columns.map(column => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead><tbody>${bodyRows}</tbody></table>
    <footer><span>LG-DTMGP &bull; Internal</span><span class="page"></span></footer>
    <script>const run=()=>setTimeout(()=>{window.focus();window.print();},150);const image=document.querySelector('img');if(image&& !image.complete){image.addEventListener('load',run);image.addEventListener('error',run)}else{run()}<\/script>
  </body></html>`);
  popup.document.close();
}
