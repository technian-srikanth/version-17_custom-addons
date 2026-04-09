{
    'name': 'PUSH NOTIFICATION',
    'depends': ['base', 'mail', 'bus'],
    'version': '17.0',
    'description': """ windows notification from odoo to user """,
    'author': 'srikanth',
    'data': [
        'views/view_mail_activity.xml',
    ],
    'assets': {
        'web.assets_backend':
            ['ts_push_notification/static/src/notification.js', ],
    }
}
