{
    'name': 'RECORD WEBHOOK AUTOMATION',
    'version': '17.0',
    'author': 'Nians',
    'depends': ['base', ],
    "website": "www.nians.com",
    'description': """ Automatically sends JSON data to a webhook whenever records are created or updated. """,
    'data': [
        'security/ir.model.access.csv',
        'views/view_webhook_config.xml',
        'views/menuitems.xml',
    ]
}
