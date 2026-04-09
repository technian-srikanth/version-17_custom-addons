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
            # 'ts_office_files_preview/static/lib/pptxjs/pptx_preview.js',
            'ts_office_files_preview/static/src/js/chatter_preview.js',
            'ts_office_files_preview/static/src/css/document_preview.css',

            # "https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js",
            # 'https://cdn.jsdelivr.net/npm/docx-preview@0.3.0/dist/docx-preview.js',

            'https://cdn.jsdelivr.net/npm/x-data-spreadsheet@1.1.5/dist/xspreadsheet.js',
            'https://cdn.jsdelivr.net/npm/x-data-spreadsheet@1.1.5/dist/xspreadsheet.css',
            'https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js'

        ],
    },
}
