# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Preview Attachments',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'author': 'Win DX JSC',
    'company': 'Win DX JSC',
    'maintainer': 'Win DX JSC',
    # 'price': 77.99,
    # 'currency': 'USD',
    # 'sequence': 110,
    'summary': 'Preview Attachments (Docx, Xlsx, Pptx, PDF, Image, Video)',
    'description': """
        User can preview attachments files: Docx, Xlsx, Pptx, PDF, Image, Video...
    """,
    'website': 'https://windx.com.vn',
    'support': 'windxcontact@gmail.com',
    'depends': ['web', 'mail', ],
    'data': [
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [

            "windx_attachments_preview/static/src/lib/docx/DocxJS.min.js",
            "windx_attachments_preview/static/src/lib/docx/DocxUiLoader.js",
            "windx_attachments_preview/static/src/lib/pdf/PdfJS.min.js",
            "windx_attachments_preview/static/src/lib/pdf/PdfUiLoader.js",
            "windx_attachments_preview/static/src/lib/pptx/SlideJS.min.js",
            "windx_attachments_preview/static/src/lib/pptx/SlideUiLoader.js",
            "windx_attachments_preview/static/src/lib/xlsx/CellJS.min.js",
            "windx_attachments_preview/static/src/lib/xlsx/CellUiLoader.js",
            # "windx_attachments_preview/static/src/attachment/attachment_list_patch.xml",
            "windx_attachments_preview/static/src/attachment/attachment_model_patch.js",
            'windx_attachments_preview/static/src/attachment_viewer/attachment_viewer_patch.js',

            "windx_attachments_preview/static/src/many2many_binary/many2many_binary_field_patch.xml",
            'windx_attachments_preview/static/src/many2many_binary/many2many_binary_field_patch.js',

        ],
        "mail.assets_messaging": [

            "windx_attachments_preview/static/src/attachment_viewer/attachment_viewer_patch.xml",
            "windx_attachments_preview/static/src/attachment_viewer/attachment_viewer_viewable_patch.js",
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
}
