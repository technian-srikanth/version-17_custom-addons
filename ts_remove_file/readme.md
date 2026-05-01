# Odoo Attachment Filestore Cleanup

## Description
This module extends Odoo’s `ir.attachment` model to remove physical attachment files
stored in the local filestore.  
It is intended for maintenance and cleanup purposes to free disk space.

---

## Features
- Identifies attachment records with files stored on disk
- Locates the active database filestore
- Deletes physical attachment files safely
- Ignores missing files without raising errors

---

## How It Works
1. Retrieves the filestore path for the current database
2. Fetches `ir.attachment` records with `store_fname`
3. Builds the absolute file path
4. Removes the physical files from the filesystem

---

## Usage
The cleanup method can be:
- Triggered manually from code or shell
- Executed via a server action
- Scheduled using a cron job

Example:
```python
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
```
