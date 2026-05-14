import io
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, models

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DynamicReportConfig(models.TransientModel):
    _name = 'dynamic.report.config'
    _description = 'Dynamic Report Config'

    def get_xlsx_report(self, data, response):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Report")
        title_fmt = workbook.add_format({
            'font_size': 12,
            'bold': True
        })
        header_fmt = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center'
        })
        text_fmt = workbook.add_format({
            'font_size': 10,
        })
        number_fmt = workbook.add_format({
            'font_size': 10,
            'align': 'right',
        })

        bold_fmt = workbook.add_format({
            'bold': True,
            'font_size': 10,
        })
        sheet.set_column(0, 0, 40)  # Name
        sheet.set_column(1, 3, 18)  # Numbers
        y = 0
        filters = data.get('filters') or {}

        for key, val in filters.items():
            if val:
                sheet.merge_range(y, 0, y, 3, str(val), title_fmt)
                y += 1

        y += 1
        sheet.write(y, 0, "Name", header_fmt)
        sheet.write(y, 1, "Debit", header_fmt)
        sheet.write(y, 2, "Credit", header_fmt)
        sheet.write(y, 3, "Balance", header_fmt)

        y += 1
        lines = data.get('lines', [])

        for line in lines:
            x = 0

            # ==========================
            # NEW OWL FORMAT (DICT)
            # ==========================
            if isinstance(line, dict) and 'name' in line:

                name = line.get('name', '')
                debit = line.get('debit', 0)
                credit = line.get('credit', 0)
                balance = line.get('balance', 0)

                # indentation support
                level = line.get('level', 0)
                indent = "    " * int(level or 0)

                sheet.write(y, x, indent + str(name), text_fmt)
                x += 1

                sheet.write(y, x, debit or 0, number_fmt)
                x += 1

                sheet.write(y, x, credit or 0, number_fmt)
                x += 1

                sheet.write(y, x, balance or 0, number_fmt)

            # ==========================
            # OLD FORMAT (DICT OF COLS)
            # ==========================
            elif isinstance(line, dict):
                for col in line.values():
                    if isinstance(col, dict):
                        value = col.get('value', '')
                        colspan = col.get('colspan', 1)
                    else:
                        value = col
                        colspan = 1

                    sheet.write(y, x, str(value), text_fmt)
                    x += colspan

            # ==========================
            # FALLBACK
            # ==========================
            else:
                sheet.write(y, 0, str(line), text_fmt)

            y += 1

        # ==============================
        # CLOSE FILE
        # ==============================
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    # =========================================================
    # MAIN ENTRY POINT
    # =========================================================
    @api.model
    def check_report(self, data):

        report_type = data.get('report_type', 'fixed')
        report_name = data['account_report_id'][0]

        data.setdefault('journal_ids', [])
        data.setdefault('used_context', {})

        company = self.env.company
        currency = company.currency_id

        currency_data = {
            'symbol': currency.symbol,
            'position': currency.position,
            'decimal_places': currency.decimal_places or 2,
            'company_id': [company.id, company.name],
        }

        # =====================================================
        # CONFIG REPORTS (Balance Sheet / P&L)
        # =====================================================
        if report_type == 'config':
            Report = self.env['report.accounting_pdf_reports.report_financial']

            data.setdefault('enable_filter', False)
            data.setdefault('debit_credit', False)
            data.setdefault('comparison', False)
            data.setdefault('date_from', data.get('date_from'))
            data.setdefault('date_to', data.get('date_to'))

            lines = Report.get_account_lines(data)

            new_lines = []

            for line in lines:

                if line.get('id'):
                    line['id'] = str(line['id'])

                # default
                line['has_child_lines'] = False

                new_lines.append(line)

                # attach move lines
                if line.get('id') and line.get('level', 0) >= 2:
                    account_id = line.get('id')

                    move_lines = self.env['account.move.line'].search([
                        ('account_id', '=', int(account_id)),
                        ('move_id.state', '=', 'posted')
                    ], limit=10)

                    if move_lines:
                        line['has_child_lines'] = True

                    for ml in move_lines:
                        new_lines.append({
                            'id': f"ml_{ml.id}",  # string
                            'parent': str(account_id),
                            'name': ml.move_name or ml.name,
                            'debit': ml.debit,
                            'credit': ml.credit,
                            'balance': ml.balance,
                            'level': (line.get('level', 0) + 1),
                            'has_child_lines': False,
                        })

            return [new_lines, currency_data]

        # =====================================================
        # PARTNER LEDGER
        # =====================================================
        if report_name == 'partner_ledger':
            Report = self.env['report.accounting_pdf_reports.report_partnerledger']

            form = {
                'form': {
                    'target_move': data.get('target_move', 'posted'),
                    'result_selection': data.get('result_selection', 'customer'),
                    'reconciled': data.get('reconciled', False),
                    'used_context': data.get('used_context', {}),
                    'partner_ids': data.get('partner_ids', []),
                },
                'computed': {},
            }

            form['computed']['move_state'] = (
                ['posted'] if form['form']['target_move'] == 'posted'
                else ['draft', 'posted']
            )

            if form['form']['result_selection'] == 'supplier':
                account_types = ['liability_payable']
            elif form['form']['result_selection'] == 'customer':
                account_types = ['asset_receivable']
            else:
                account_types = ['asset_receivable', 'liability_payable']

            self.env.cr.execute("""
                                SELECT id
                                FROM account_account
                                WHERE account_type IN %s
                                  AND NOT deprecated
                                """, (tuple(account_types),))

            form['computed']['account_ids'] = [x[0] for x in self.env.cr.fetchall()]

            partners = self.env['res.partner'].search([])

            lines = []

            for partner in partners.sorted(key=lambda p: (p.ref or '', p.name or '')):
                debit = Report._sum_partner(form, partner, 'debit')
                credit = Report._sum_partner(form, partner, 'credit')

                lines.append({
                    'line_type': 'partner_parent',
                    'id': f"partner_{partner.id}",
                    'name': partner.display_name,
                    'partner': partner.id,

                    'debit': debit,
                    'credit': credit,
                    'balance': debit - credit,

                    'parent': None,
                    'level': 0,
                    'has_child_lines': True,
                })

            return [lines, currency_data]
        # =====================================================
        # GENERAL LEDGER
        # =====================================================
        if report_name == 'general_ledger':
            Report = self.env['report.accounting_pdf_reports.report_general_ledger']

            accounts = self.env['account.account'].search([])

            report_lines = Report.with_context(
                data['used_context']
            )._get_account_move_entry(
                accounts,
                False,
                False,
                data.get('initial_balance', False),
                data.get('sortby', 'sort_date'),
                data.get('display_account', 'movement'),
            )

            prev_ids = {}

            for line in report_lines:
                line['id'] = str(line.get('id'))

                level = line.get('level', 0)

                if level == 0:
                    line['parent'] = None
                else:
                    line['parent'] = prev_ids.get(level - 1)

                prev_ids[level] = line['id']

                line['has_child_lines'] = True

            return [report_lines, currency_data]

        # =====================================================
        # JOURNALS AUDIT
        # =====================================================
        if report_name == 'journals_audit':

            lines = []

            moves = self.env['account.move.line'].search([
                ('move_id.state', '=', data.get('target_move', 'posted'))
            ], limit=200)

            for ml in moves:
                lines.append({
                    'id': str(ml.id),
                    'name': ml.move_name or '/',
                    'debit': ml.debit,
                    'credit': ml.credit,
                    'balance': ml.balance,
                    'level': 0,
                    'parent': None,
                    'has_child_lines': False,
                })

            return [lines, currency_data]

        # =====================================================
        # TRIAL BALANCE
        # =====================================================
        if report_name == 'trial_balance':
            Report = self.env['report.accounting_pdf_reports.report_trialbalance']

            accounts = self.env['account.account'].search([])

            report_lines = Report.with_context(
                data['used_context']
            )._get_accounts(accounts, data.get('display_account', 'all'))

            prev_ids = {}

            for line in report_lines:
                line['id'] = str(line.get('id'))

                level = line.get('level', 0)

                if level == 0:
                    line['parent'] = None
                else:
                    line['parent'] = prev_ids.get(level - 1)

                prev_ids[level] = line['id']

                line['has_child_lines'] = True

            return [report_lines, currency_data]

        # =====================================================
        # =====================================================
        # =====================================================
        # AGED PARTNER
        # =====================================================
        # =====================================================
        # AGED PARTNER
        # =====================================================
        if report_name == 'aged_partner':

            Report = self.env[
                'report.accounting_pdf_reports.report_agedpartnerbalance'
            ]

            # ==========================================
            # DEFAULTS
            # ==========================================
            if not data.get('date_from'):
                data['date_from'] = time.strftime('%Y-%m-%d')

            data.setdefault('target_move', 'posted')
            data.setdefault('result_selection', 'customer')
            data.setdefault('period_length', 30)

            # ==========================================
            # ACCOUNT TYPE (ODOO 17)
            # ==========================================
            if data.get('result_selection') == 'customer':

                account_type = ['asset_receivable']

            elif data.get('result_selection') == 'supplier':

                account_type = ['liability_payable']

            elif data.get('result_selection') == 'customer_supplier':

                account_type = [
                    'asset_receivable',
                    'liability_payable'
                ]

            else:

                account_type = [
                    'asset_receivable',
                    'liability_payable'
                ]

            # ==========================================
            # FETCH DATA
            # ==========================================
            movelines, total, dummy = Report._get_partner_move_lines(
                account_type,
                [],

                data['date_from'],
                data['target_move'],
                data['period_length']
            )

            # ==========================================
            # DEBUG
            # ==========================================

            if not movelines:
                print("NO MOVELINES FOUND")

            lines = []

            # ==========================================
            # BUILD LINES
            # ==========================================
            for i, line in enumerate(movelines):

                partner_id = line.get('partner_id') or i

                not_due = line.get('direction', 0)

                bucket_0_30 = line.get('0', 0)
                bucket_30_60 = line.get('1', 0)
                bucket_60_90 = line.get('2', 0)
                bucket_90_120 = line.get('3', 0)
                bucket_120 = line.get('4', 0)

                total_amount = line.get('total', 0)

                # ==========================================
                # MAIN ROW
                # ==========================================
                lines.append({
                    'id': f"partner_{partner_id}",

                    'name': line.get('name', ''),

                    # GENERIC TABLE MAPPING
                    'debit': not_due,
                    'credit': bucket_0_30,
                    'balance': total_amount,

                    'level': 0,
                    'parent': None,

                    'has_child_lines': False,
                })

                # ==========================================
                # EXTRA AGING BUCKETS
                # ==========================================
                aging_rows = [
                    ("30-60", bucket_30_60),
                    ("60-90", bucket_60_90),
                    ("90-120", bucket_90_120),
                    ("120+", bucket_120),
                ]

                for label, amount in aging_rows:

                    if not amount:
                        continue

                    lines.append({
                        'id': f"{partner_id}_{label}",

                        'name': f"   {label}",

                        'debit': 0,
                        'credit': amount,
                        'balance': amount,

                        'level': 1,
                        'parent': None,

                        'has_child_lines': False,
                    })

            return [lines, currency_data]
        # TAX REPORT
        # =====================================================
        # =====================================================
        # TAX REPORT
        # =====================================================
        # =====================================================
        # TAX REPORT
        # =====================================================
        if report_name == 'tax_report':

            journal_ids = data.get('journal_ids', [])
            tax_type = data.get('tax_type', 'all')

            domain = [
                ('tax_line_id', '!=', False),
            ]

            # ==========================================
            # DATE FILTER
            # ==========================================
            if data.get('date_from'):
                domain.append((
                    'date',
                    '>=',
                    data.get('date_from')
                ))

            if data.get('date_to'):
                domain.append((
                    'date',
                    '<=',
                    data.get('date_to')
                ))

            # ==========================================
            # JOURNAL FILTER
            # ==========================================
            if journal_ids:
                domain.append((
                    'journal_id',
                    'in',
                    journal_ids
                ))

            # ==========================================
            # POSTED FILTER
            # ==========================================
            if data.get('target_move') == 'posted':
                domain.append((
                    'move_id.state',
                    '=',
                    'posted'
                ))

            # ==========================================
            # SALE FILTER
            # ==========================================
            if tax_type == 'sale':

                domain.append((
                    'move_id.move_type',
                    'in',
                    ['out_invoice', 'out_refund']
                ))

            # ==========================================
            # PURCHASE FILTER
            # ==========================================
            elif tax_type == 'purchase':

                domain.append((
                    'move_id.move_type',
                    'in',
                    ['in_invoice', 'in_refund']
                ))

            # ==========================================
            # FETCH TAX LINES
            # ==========================================
            move_lines = self.env['account.move.line'].search(domain)

            lines = []
            grouped = {}

            # ==========================================
            # GROUP TAXES
            # ==========================================
            for ml in move_lines:

                tax = ml.tax_line_id

                if not tax:
                    continue

                key = tax.id

                if key not in grouped:
                    grouped[key] = {
                        'name': tax.name,
                        'net': 0.0,
                        'tax': 0.0,
                    }

                grouped[key]['tax'] += abs(ml.balance)

                if ml.tax_base_amount:
                    grouped[key]['net'] += abs(ml.tax_base_amount)

            # ==========================================
            # BUILD RESULT
            # ==========================================
            for tax_id, vals in grouped.items():
                net = vals['net']
                tax = vals['tax']

                lines.append({
                    'id': str(tax_id),

                    'name': vals['name'],

                    'debit': net,
                    'credit': tax,
                    'balance': net + tax,

                    'level': 0,
                    'parent': None,

                    'has_child_lines': False,
                })

            return [lines, currency_data]

    # =========================================================
    # LAZY LOADER FOR PARTNER LEDGER
    # =========================================================
    @api.model
    def fetch_partner_ledger_lines(self, partner_id, filters):
        Report = self.env["report.accounting_pdf_reports.report_partnerledger"]

        form = {
            "form": {
                "target_move": filters.get("target_move", "posted"),
                "result_selection": filters.get("result_selection", "customer"),
                "reconciled": filters.get("reconciled", False),
                "used_context": filters.get("used_context", {}),
                "partner_ids": [partner_id],
            },
            "computed": {},
        }

        form["computed"]["move_state"] = ["posted"]

        self.env.cr.execute("""
                            SELECT id
                            FROM account_account
                            WHERE account_type IN ('asset_receivable', 'liability_payable')
                              AND NOT deprecated
                            """)
        form["computed"]["account_ids"] = [x[0] for x in self.env.cr.fetchall()]

        partner = self.env["res.partner"].browse(partner_id)
        children = Report._lines(form, partner)

        fixed_lines = []

        for idx, line in enumerate(children):

            raw_id = line.get('id') or f"{partner_id}_{idx}"
            line_id = f"ml_{raw_id}"

            if line.get('parent'):
                parent = f"ml_{line.get('parent')}"
            else:
                parent = f"partner_{partner_id}"

            fixed_lines.append({
                **line,
                'id': line_id,
                'parent': parent,
                'has_child_lines': False,
            })

        return fixed_lines

    @api.model
    def print_pdf(self, data):
        return self.env.ref(
            'om_dynamic_reports.report_account_reports_pdf'
        ).report_action(
            [self.env.company.id],
            data=data
        )


class ReportDynamic(models.AbstractModel):
    _name = 'report.om_dynamic_reports.om_account_reports_pdf'

    def _get_report_values(self, docids, data=None):
        if not docids:
            docids = [self.env.company.id]

        docs = self.env['res.company'].browse(docids)

        return {
            'docs': docs,
            'data': data,
        }
