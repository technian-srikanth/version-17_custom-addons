{
    'name': 'Attachment files preview',
    'version': '17.0.0.0.1',
    'depends': ['base', 'mail', 'web', ],
    'author': 'Nians',
    'description': """ CSV ,XLSX ,PPTX AND  DOCX Attachments files preview """,
    "data": ['data/ir_cron.xml', ],
    'assets': {
        'web.assets_backend': [
            'ts_office_files_preview/static/lib/jszip.min.js',

            'ts_office_files_preview/static/src/js/chatter_preview.js',
            'ts_office_files_preview/static/src/css/document_preview.css',

            # preview xls and csv
            "ts_office_files_preview/static/lib/xls/spreadheet.js",
            "ts_office_files_preview/static/src/css/spreadhseet.css",
            "ts_office_files_preview/static/lib/xls/xlsx.full.min.js",

            # preview pptx and  Docx
            "ts_office_files_preview/static/lib/pdf.mjs",
            "ts_office_files_preview/static/lib/pdf.worker.mjs",
        ],
    },
}
