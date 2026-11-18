frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["DTMGP Workforce Breakdown"] = {
	method: "dtmgp.dtmgp.dashboard_chart_source.dtmgp_workforce_breakdown.dtmgp_workforce_breakdown.get_data",
	filters: [
		{
			fieldname: "company",
			label: __("LGA"),
			fieldtype: "Link",
			options: "Company",
			description: __("Leave empty for every LGA you are permitted to see"),
		},
	],
};
