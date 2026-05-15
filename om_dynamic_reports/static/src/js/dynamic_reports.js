/** @odoo-module **/

import {Component, onWillStart, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {download} from "@web/core/network/download";
import {patch} from "@web/core/utils/patch";
import {Many2XAutocomplete} from "@web/views/fields/relational_utils";

export class DynamicReports extends Component {
    static components = {
        Many2XAutocomplete,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.company = useService("company");
        this.addJournal = this.addJournal.bind(this);
        this.removeJournal = this.removeJournal.bind(this);

        this.state = useState({
            loading: false,
            report_type: [],
            journal_ids: [],
            filters: {
                account_report_id: null,
                date_from: null,
                date_to: null,
                journal_ids: [],
                target_move: "posted",
                company_id: this.company.currentCompany.id,
            },
            report_lines: [],
            currency: {},
            expandedLines: {},
            loadedChildren: {},
            loadingChildrenKey: null,
            context: {},
            activeFilters: [],
            requiredFilters: [],
        });
        this.toggle = this.toggle.bind(this);
        this.getLineKey = this.getLineKey.bind(this);
        this.isVisible = this.isVisible.bind(this);
        this.openLine = this.openLine.bind(this);

        onWillStart(() => this.loadInitialData());
    }

    /* =========================================================
     * INITIAL DATA
     * ========================================================= */

    async loadInitialData() {
        const reports = await this.orm.searchRead(
            "account.financial.report",
            [["parent_id", "=", false]],
            ["name"]
        );

        this.state.report_type = [
            ...reports,
            {id: "journals_audit", name: "Journals Audit"},
            {id: "partner_ledger", name: "Partner Ledger"},
            {id: "general_ledger", name: "General Ledger"},
            {id: "trial_balance", name: "Trial Balance"},
            {id: "aged_partner", name: "Aged Partner Balance"},
            {id: "tax_report", name: "Tax Report"},
        ];

        this.state.journal_ids = await this.orm.searchRead(
            "account.journal",
            [],
            ["name"]
        );
    }

    /* =========================================================
     * INPUT HANDLER
     * ========================================================= */

    onInputChange(ev) {
        const el = ev.target;
        const name = el.name;

        if (el.multiple) {
            this.state.filters[name] =
                [...el.selectedOptions].map(o => parseInt(o.value));
        } else {
            this.state.filters[name] =
                el.type === "checkbox" ? el.checked : el.value || null;
        }
    }

    updateJournalIds(records) {

        this.state.filters.journal_ids =
            records.map(r => r.id);

        console.log(
            'selected journals',
            this.state.filters.journal_ids
        );
    }

    getJournalDomain() {
        return [];
    }

    addJournal(ev) {

        const id = parseInt(ev.target.value);

        if (!id) {
            return;
        }

        const ids = this.state.filters.journal_ids || [];

        if (!ids.includes(id)) {

            this.state.filters.journal_ids = [
                ...ids,
                id,
            ];
        }

        // reset select
        ev.target.value = "";
    }

    removeJournal(id) {

        this.state.filters.journal_ids =
            (this.state.filters.journal_ids || [])
                .filter(j => j !== id);
    }

    /* =========================================================
     * REPORT TYPE HELPER
     * ========================================================= */

    getReportType(reportId) {
        // numeric → Balance Sheet / P&L
        // string  → fixed reports
        return Number.isInteger(Number(reportId)) ? "config" : "fixed";
    }

    /* =========================================================
     * FETCH REPORT
     * ========================================================= */


    async fetchReport() {
        if (!this.state.filters.account_report_id) return;

        this.state.loading = true;
        this.state.report_lines = [];
        this.state.expandedLines = {};

        const payload = this._buildPayload();

        const [lines, currency] = await this.orm.call(
            "dynamic.report.config",
            "check_report",
            [payload]
        );

        this.state.report_lines = lines || [];
        this.state.currency = currency || {};
        this.state.loading = false;
    }

    _buildPayload() {
        const reportId = this.state.filters.account_report_id;
        const reportType = this.getReportType(reportId);

        return {
            report_type: reportType,

            account_report_id: reportType === "config"
                ? [parseInt(reportId), "Config Report"]
                : [reportId, reportId.replaceAll("_", " ").toUpperCase()],

            date_from: this.state.filters.date_from || false,
            date_to: this.state.filters.date_to || false,
            journal_ids: this.state.filters.journal_ids || [],
            target_move: this.state.filters.target_move || "posted",

            display_account: this.state.filters.display_account,
            sortby: this.state.filters.sortby,
            result_selection: this.state.filters.result_selection || "customer",
            reconciled: this.state.filters.reconciled,
            period_length: this.state.filters.period_length || 30,

            company_id: this.state.filters.company_id,

            used_context: {
                journal_ids: this.state.filters.journal_ids || [],
                date_from: this.state.filters.date_from || false,
                date_to: this.state.filters.date_to || false,
                state: this.state.filters.target_move || "posted",
                company_id: this.state.filters.company_id,
            },
        };
    }

    /* =========================================================
     * DRILL DOWN
     * ========================================================= */

    openLine(line) {
        if (!line.res_id || line.res_id <= 0) return;

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.move.line",
            res_id: line.res_id,
            views: [[false, "form"]],
            target: "current",
        });
    }


    getLineKey(line, index) {
        return line.partner
            ? `partner_${line.partner}`
            : `line_${index}`;
    }


    async toggle(line, index) {
        if (!line) return;

        const key = line._key;

        console.log('key', key);

        if (line.line_type === "partner_parent") {

            if (!(key in this.state.loadedChildren)) {

                const children = await this.orm.call(
                    "dynamic.report.config",
                    "fetch_partner_ledger_lines",
                    [line.partner, this.state.filters]
                );

                this.state.loadedChildren = {
                    ...this.state.loadedChildren,
                    [key]: children || [],
                };
            }
        }

        this.state.expandedLines = {
            ...this.state.expandedLines,
            [key]: !this.state.expandedLines[key],
        };
    }

    async _printPdf() {
        const payload = this._buildPayload();

        // fetch report data
        const [lines, currency] = await this.orm.call(
            "dynamic.report.config",
            "check_report",
            [payload]
        );

        payload.lines = lines;
        payload.currency = currency;

        console.log("payload", payload);

        const action = await this.orm.call(
            "dynamic.report.config",
            "print_pdf",
            [payload]
        );

        this.env.services.action.doAction(action);
    }


    async _printXlsx() {
        if (!this.state.filters.account_report_id) return;

        const payload = this._buildPayload();

        await this.env.services.ui.block();

        try {
            // get fresh report lines
            const [lines] = await this.orm.call(
                "dynamic.report.config",
                "check_report",
                [payload]
            );

            await download({
                url: "/report_xlsx",
                data: {
                    model: "dynamic.report.config",
                    options: JSON.stringify({
                        filters: this._formatReportInput(),
                        lines: lines,
                    }),
                    output_format: "xlsx",
                    report_name: "Dynamic Report",
                },
            });

        } finally {
            this.env.services.ui.unblock();
        }
    }

    _formatReportInput() {
        const f = this.state.filters;

        return {
            date_from: f.date_from ? `From: ${f.date_from}` : "",
            date_to: f.date_to ? `To: ${f.date_to}` : "",
        };
    }

    isVisible(line) {
        if (!line.parent) return true;

        // config reports
        if (typeof line.parent === "number") {
            return !!this.state.expandedLines[line.parent];
        }

        // partner ledger
        const parentKey = `partner_${line.parent}`;
        return !!this.state.expandedLines[parentKey];
    }

    /* =========================================================
     * FORMATTERS
     * ========================================================= */

    formatAmount(value) {
        if (typeof value !== "number") return value;

        const digits = this.state.currency?.decimal_places ?? 2;
        let v = value.toFixed(digits);

        if (!this.state.currency?.symbol) return v;

        return this.state.currency.position === "after"
            ? `${v} ${this.state.currency.symbol}`
            : `${this.state.currency.symbol} ${v}`;
    }

    getDisplayLines() {

        const result = [];
        const lines = this.state.report_lines || [];

        let hiddenLevels = {};

        for (let i = 0; i < lines.length; i++) {

            const line = lines[i];

            const level = line.level || 0;

            // hide if parent collapsed
            let visible = true;

            for (const lvl in hiddenLevels) {
                if (level > lvl && hiddenLevels[lvl]) {
                    visible = false;
                }
            }

            const key = `line_${i}`;

            const nextLine = lines[i + 1];

            const hasChildren =
                nextLine &&
                (nextLine.level || 0) > level;

            result.push({
                ...line,
                _key: key,
                _type: hasChildren ? "parent" : "child",
                has_child_lines: hasChildren,
                visible: visible,
                _index: i,
            });

            hiddenLevels[level] =
                !this.state.expandedLines[key];
        }

        return result.filter(r => r.visible);
    }
}

DynamicReports.template = "om_dynamic_reports.DynamicReports";

registry.category("actions").add(
    "dynamic_reports_view",
    DynamicReports
);

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
                    "journal_ids",

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