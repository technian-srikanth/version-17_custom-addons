from odoo import models, api
from odoo.tools import config
from pathlib import Path
import os


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def remove_old_attachments(self):
        file_store = config.filestore(self._cr.dbname)
        attachments = self.env['ir.attachment'].search([('store_fname', '!=', False)])
        for attachment in attachments:
            if attachment.store_fname:
                clean_fname = attachment.store_fname.replace('/', os.sep)
                full_path = Path(file_store) / clean_fname
                print("Attachment:", attachment.id, full_path)
                if full_path:
                    full_path.unlink(missing_ok=True)
                    print('removed:', full_path)
                else:
                    print('path not found:')
