frappe.query_reports["LGA Workforce Comparison"] = {
	filters: [
		{
			fieldname: "company",
			label: __("LGA"),
			fieldtype: "Link",
			options: "Company",
			description: __("Leave empty to compare every LGA you are permitted to see"),
		},
		{
			fieldname: "hide_empty",
			label: __("Hide LGAs with no staff records"),
			fieldtype: "Check",
			default: 0,
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold) value = `<b>${value}</b>`;
		return value;
	},
};
