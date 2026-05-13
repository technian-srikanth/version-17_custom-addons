/** @odoo-module **/

import {Component, onWillStart, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {download} from "@web/core/network/download";
import {patch} from "@web/core/utils/patch";

export class DynamicReports extends Component {

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.company = useService("company");

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
            result_selection: this.state.filters.result_selection,
            reconciled: this.state.filters.reconciled,
            period_length: this.state.filters.period_length,

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

    // async toggle(line, index) {
    //     if (!line) return;
    //
    //     let key;
    //
    //     // ✅ config reports (P&L, BS)
    //     if (line.id !== undefined) {
    //         key = line.id;
    //     }
    //     // ✅ partner ledger
    //     else if (line.partner) {
    //         key = `partner_${line.partner}`;
    //     } else {
    //         key = this.getLineKey(line, index);
    //     }
    //
    //     // 👉 partner ledger lazy loading
    //     if (line.line_type === "partner_parent") {
    //         if (this.state.loadingChildrenKey === key) return;
    //
    //         this.state.loadingChildrenKey = key;
    //
    //         try {
    //             if (!(key in this.state.loadedChildren)) {
    //                 const children = await this.orm.call(
    //                     "dynamic.report.config",
    //                     "fetch_partner_ledger_lines",
    //                     [line.partner, this.state.filters]
    //                 );
    //
    //                 this.state.loadedChildren = {
    //                     ...this.state.loadedChildren,
    //                     [key]: children || [],
    //                 };
    //             }
    //         } finally {
    //             this.state.loadingChildrenKey = null;
    //         }
    //     }

    //
    //     // ✅ toggle expand
    //     this.state.expandedLines = {
    //         ...this.state.expandedLines,
    //         [key]: !this.state.expandedLines[key],
    //     };
    // }


    async toggle(line, index) {
        if (!line) return;

        let key = line.id
            ? String(line.id)
            : line.partner
                ? `partner_${line.partner}`
                : String(this.getLineKey(line, index));

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

        // helper: normalize id to string (handles numbers + "ml_..." ids)
        const toKey = (v) => (v === undefined || v === null ? null : String(v));

        // group children by parent for fast lookup
        const byParent = {};
        for (const l of lines) {
            const p = toKey(l.parent);
            if (!p) continue;
            if (!byParent[p]) byParent[p] = [];
            byParent[p].push(l);
        }

        // recursive renderer
        const addChildren = (parentId) => {
            const pKey = toKey(parentId);
            let children = [...(byParent[pKey] || [])];

            if (this.state.loadedChildren[pKey]) {
                children.push(...this.state.loadedChildren[pKey]);
            }

            for (const child of children) {
                const cKey = toKey(child.id);

                const hasChildren = !!byParent[cKey]?.length;

                result.push({
                    ...child,
                    _type: "child",
                    _key: cKey,              // 🔥 unique per row
                    has_child_lines: hasChildren,
                });

                // expand ONLY this node’s subtree
                if (this.state.expandedLines[cKey]) {
                    addChildren(child.id);
                }
            }
        };

        // ROOT LEVEL (only lines with no parent)
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            if (line.parent !== undefined && line.parent !== null) continue;

            const key = line.id
                ? String(line.id)
                : line.partner
                    ? `partner_${line.partner}`
                    : String(this.getLineKey(line, i));

            const hasChildren = !!byParent[key]?.length;

            result.push({
                ...line,
                _type: "parent",
                _key: key,
                _index: i,
                has_child_lines: hasChildren,
            });

            if (this.state.expandedLines[key]) {
                addChildren(line.id);
            }
        }

        return result;
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