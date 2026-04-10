{
    'name': 'RECORD DATA IN JSON ',
    'version': '17.0',
    'author': 'srikanth',
    'depends': ['base', ],
    'description': """ Automatically sends JSON data to a webhook whenever records are created or updated. """,
    'data': [
        'security/ir.model.access.csv',
        'views/view_webhook_config.xml',
        'views/menuitems.xml',
    ]
}
