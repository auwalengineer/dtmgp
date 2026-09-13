(function () {
	function renameCompanyNavigationLabel(root) {
		const scope = root || document;
		scope.querySelectorAll(".desk-sidebar .sidebar-item-label, .desk-sidebar a").forEach(function (item) {
			if (item.textContent.trim() === "Company") {
				item.textContent = "LGA";
			}
		});
	}

	function initializeDeskBranding() {
		renameCompanyNavigationLabel();
		new MutationObserver(function (mutations) {
			mutations.forEach(function (mutation) {
				mutation.addedNodes.forEach(function (node) {
					if (node.nodeType === Node.ELEMENT_NODE) {
						renameCompanyNavigationLabel(node);
					}
				});
			});
		}).observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", initializeDeskBranding);
	} else {
		initializeDeskBranding();
	}
})();