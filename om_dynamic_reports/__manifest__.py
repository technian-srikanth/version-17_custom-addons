# -*- coding: utf-8 -*-
# License: Odoo Proprietary License v1.0

{
    'name': 'Odoo 16 Dynamic Accounting Reports - PDF, Excel',
    'version': '17.0.3.0.0',
    'category': 'Invoicing Management',
    'summary': 'All in One Dynamic Accounting Reports For Odoo & '
               'Export the Report in PDF or Excel',
    'sequence': '10',
    'website': 'https://www.youtube.com/c/OdooMates/videos',
    'live_test_url': 'https://www.youtube.com/watch?v=XA-MzpIE0lQ',
    'author': 'Odoo Mates',
    'license': 'OPL-1',
    'price': 55,
    'currency': 'USD',
    'maintainer': 'Odoo Mates',
    'support': 'odoomates@gmail.com',
    'depends': ["web", 'accounting_pdf_reports'],
    'data': [
        'security/ir.model.access.csv',
        'views/dynamic_reports.xml',
        'views/settings.xml',
        'report/report_om_account_pdf.xml',
        'report/reports.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'om_dynamic_reports/static/src/css/report_controller.css',
            'om_dynamic_reports/static/src/js/jquery-resizable.js',
            'om_dynamic_reports/static/src/js/dynamic_reports.js',
            'om_dynamic_reports/static/src/js/dynamic_report_actions.js',
            'om_dynamic_reports/static/src/xml/report_control.xml',
        ],
        'web.report_assets_common': [
            'om_dynamic_reports/static/src/css/report_controller.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/trial_balance_report.gif'],
}
