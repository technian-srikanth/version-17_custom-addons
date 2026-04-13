from odoo import models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def send_notification(self):
        params = {
            "title": "Scheduled Updates",
            "message": "Periodic report is ready.",
            'link':  '/web/login',
            'image': '/ts_push_notification/static/description/icon.png',
        }

        if self.user_id:
            self.env['bus.bus']._sendone(
                self.user_id.partner_id,
                "activity_notification",
                params
            )
