/* Hotel Compliance Tracker — minimal vanilla JS */

document.addEventListener("DOMContentLoaded", function () {

    /* ── Expandable rows ───────────────────────────────────────────────── */
    document.querySelectorAll(".expand-toggle").forEach(function (toggle) {
        toggle.addEventListener("click", function () {
            var targetId = this.dataset.target;
            var content = document.getElementById(targetId);
            if (content) {
                content.classList.toggle("expanded");
                this.classList.toggle("expanded");
            }
        });
    });

    /* ── Modal open/close ──────────────────────────────────────────────── */
    document.querySelectorAll("[data-modal]").forEach(function (trigger) {
        trigger.addEventListener("click", function (e) {
            e.preventDefault();
            var modalId = this.dataset.modal;
            var modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add("active");
                // Copy permit ID to hidden field if present
                var permitId = this.dataset.permitId;
                if (permitId) {
                    var form = modal.querySelector("form");
                    if (form) {
                        form.action = form.action.replace("__PERMIT_ID__", permitId);
                    }
                }
            }
        });
    });

    document.querySelectorAll(".modal-close, .modal-cancel").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var overlay = this.closest(".modal-overlay");
            if (overlay) overlay.classList.remove("active");
        });
    });

    document.querySelectorAll(".modal-overlay").forEach(function (overlay) {
        overlay.addEventListener("click", function (e) {
            if (e.target === overlay) overlay.classList.remove("active");
        });
    });

    /* ── Flash message auto-dismiss ────────────────────────────────────── */
    document.querySelectorAll(".flash").forEach(function (flash) {
        setTimeout(function () {
            flash.style.opacity = "0";
            flash.style.transition = "opacity .3s";
            setTimeout(function () { flash.remove(); }, 300);
        }, 5000);
    });

    /* ── Confirm actions ───────────────────────────────────────────────── */
    document.querySelectorAll("[data-confirm]").forEach(function (el) {
        el.addEventListener("click", function (e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    /* ── Sort dropdown for dashboard ───────────────────────────────────── */
    var sortSelect = document.getElementById("sort-select");
    if (sortSelect) {
        sortSelect.addEventListener("change", function () {
            var sections = {
                "expired": document.getElementById("section-expired"),
                "upcoming": document.getElementById("section-upcoming"),
                "compliant": document.getElementById("section-compliant"),
            };
            // Show all, then reorder
            Object.values(sections).forEach(function (s) {
                if (s) s.style.order = "0";
            });
            var val = this.value;
            if (val && sections[val]) {
                sections[val].style.order = "-1";
            }
        });
    }

    /* ── Permit type autocomplete for add permit ───────────────────────── */
    var permitTypeSelect = document.getElementById("permit-type-select");
    var customNameInput = document.getElementById("custom-name-input");
    if (permitTypeSelect && customNameInput) {
        permitTypeSelect.addEventListener("change", function () {
            if (this.value) {
                customNameInput.value = "";
                customNameInput.disabled = true;
            } else {
                customNameInput.disabled = false;
            }
        });
    }
});
