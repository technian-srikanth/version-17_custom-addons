/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import DynamicReports from "om_dynamic_reports.DynamicReports";

/**
 * ACTION SELECTION + REPORT SWITCH (ODOO 17)
 */
patch(DynamicReports.prototype, {

    /* =====================================
     * ACTION DROPDOWN HANDLER
     * ===================================== */
    selectAction(ev) {
        const actionId = ev.currentTarget.dataset.action;
        const rowId = Number(ev.currentTarget.closest("tr")?.dataset?.id);

        if (!actionId || !rowId) return;

        this.state.context.sel_account_ids = [rowId];
        this.state.context.act_id = actionId;

        this.setReport(actionId);
        this.fetchReport();
    },

    /* =====================================
     * REPORT SWITCHER
     * ===================================== */
    setReport(reportId) {
        const report = this.state.report_type.find(r => r.id === reportId);
        if (!report) return;

        // ✅ SAFE mutation (do NOT replace object)
        Object.assign(this.state.filters, {
            account_report_id: reportId,
        });

        this.state.currentReportName = report.name;
        this.state.activeFilters = [];
        this.state.requiredFilters = [];

        switch (reportId) {

            case "journals_audit":
                this._enableFilters([
                    "target_move",
                    "sort_selection",
                    "date_from",
                    "date_to",
                    "journal_ids",
                ]);
                break;

            case "partner_ledger":
                this._enableFilters([
                    "target_move",
                    "result_selection",
                    "reconciled",
                    "date_from",
                    "date_to",
                    "journal_ids",
                ]);
                break;

            case "general_ledger":
                this._enableFilters([
                    "target_move",
                    "sortby",
                    "display_account",
                    "initial_balance",
                    "date_from",
                    "date_to",
                    "journal_ids",
                ]);
                break;

            case "trial_balance":
                this._enableFilters([
                    "target_move",
                    "display_account",
                    "date_from",
                    "date_to",
                ]);
                break;

            case "aged_partner":
                this._enableFilters([
                    "target_move",
                    "result_selection",
                    "date_from",
                    "period_length",
                ]);
                this._markRequired(["date_from", "period_length"]);
                break;

            case "tax_report":
                this._enableFilters([
                    "date_from",
                    "date_to",
                    "target_move",
                ]);
                this._markRequired(["date_from", "date_to"]);
                break;

            default:
                this._enableFilters([
                    "target_move",
                    "debit_credit",
                    "date_from",
                    "date_to",
                ]);
        }
    },

    /* =====================================
     * FILTER HELPERS
     * ===================================== */
    _enableFilters(fields) {
        this.state.activeFilters = fields;
    },

    _markRequired(fields) {
        this.state.requiredFilters = fields;
    },
});