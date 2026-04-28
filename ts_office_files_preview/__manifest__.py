{
    'name': 'Attachment',
    'version': '17.0',
    'depends': ['web', 'base', 'mail', ],
    'author': 'srikanth',
    'description': """ CSV ,XLSX AND DOCX FILES PREVIEW IN CHATTER """,
    'assets': {
        'web.assets_backend': [
            'ts_office_files_preview/static/lib/jszip.min.js',
            'ts_office_files_preview/static/lib/dock-preview.js',
            'ts_office_files_preview/static/src/js/chatter_preview.js',
            # 'https://cdn.jsdelivr.net/npm/x-data-spreadsheet@1.1.5/dist/xspreadsheet.js',
            "ts_office_files_preview/static/lib/xls/spreadheet.js",
            # 'https://cdn.jsdelivr.net/npm/x-data-spreadsheet@1.1.5/dist/xspreadsheet.css',
            "ts_office_files_preview/static/src/css/spreadhseet.css",
            # 'https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js',
            "ts_office_files_preview/static/lib/xls/xlsx.full.min.js",

            # "ts_office_files_preview/static/lib/pdf.mjs",
            # "ts_office_files_preview/static/lib/pdf.worker.mjs",

            "ts_office_files_preview/static/lib/pptx/SlideJS.min.js",
            "ts_office_files_preview/static/lib/pptx/SlideUiLoader.js",
            'ts_office_files_preview/static/src/css/document_preview.css',

            "https://unpkg.com/mammoth/mammoth.browser.min.js",

        ],
    },
}
