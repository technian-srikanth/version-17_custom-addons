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
            'ts_office_files_preview/static/src/css/document_preview.css',
            # 'https://cdn.jsdelivr.net/npm/x-data-spreadsheet@1.1.5/dist/xspreadsheet.js',
            "ts_office_files_preview/static/lib/xls/spreadheet.js",
            # 'https://cdn.jsdelivr.net/npm/x-data-spreadsheet@1.1.5/dist/xspreadsheet.css',
            "ts_office_files_preview/static/src/css/spreadhseet.css",
            # 'https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js',
            "ts_office_files_preview/static/lib/xls/xlsx.full.min.js",


            # "ts_office_files_preview/static/lib/filereader.js",
            # "ts_office_files_preview/static/lib/pptxjs.min.js",
            # "ts_office_files_preview/static/src/css/pptxjs.css",
            # 'ts_office_files_preview/static/lib/pptxjs/jszip.min.js',
            # "ts_office_files_preview/static/lib/pptxjs/pptxjs.js",
            #
            # "ts_office_files_preview/static/lib/pdf.mjs",
            # "ts_office_files_preview/static/lib/pdf.worker.mjs",
        ],
    },
}
