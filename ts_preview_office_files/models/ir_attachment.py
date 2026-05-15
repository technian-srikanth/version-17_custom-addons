from odoo import models, api
import base64
import tempfile
import subprocess
import os
import platform
import shutil

if platform.system() == "Windows":
    LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"
else:
    LIBREOFFICE_PATH = shutil.which("soffice") or "/usr/bin/soffice"

if not os.path.exists(LIBREOFFICE_PATH):
    raise Exception(
        f"LibreOffice not found: {LIBREOFFICE_PATH}"
    )


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _convert_to_pdf_with_cache(self, ext):

        self.ensure_one()

        if not self.datas:
            raise Exception("Attachment has no data")

        cache_key = f"{self.id}_{self.checksum}"
        cached_name = f"cache_{cache_key}.pdf"

        preview_cache = self.env['ir.attachment'].sudo().search([
            ('name', '=', cached_name),
        ], limit=1)

        if preview_cache:
            return base64.b64decode(preview_cache.datas)

        old_caches = self.env['ir.attachment'].sudo().search([
            ('name', 'like', f"cache_{self.id}_")
        ])

        old_caches.unlink()

        file_data = base64.b64decode(self.datas)

        with tempfile.TemporaryDirectory() as tmpdir:

            input_path = os.path.join(tmpdir, f"input.{ext}")

            with open(input_path, "wb") as f:
                f.write(file_data)

            if os.path.getsize(input_path) == 0:
                raise Exception("Input file is empty")

            libreoffice_profile = os.path.join(
                tmpdir,
                "lo_profile"
            )

            os.makedirs(
                libreoffice_profile,
                exist_ok=True
            )

            process = subprocess.run([
                LIBREOFFICE_PATH,

                f'-env:UserInstallation=file:///{libreoffice_profile.replace(os.sep, "/")}',

                '--headless',
                '--nologo',
                '--nofirststartwizard',
                '--nolockcheck',
                '--nodefault',
                '--convert-to',
                'pdf',
                '--outdir',
                tmpdir,
                input_path,
            ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if process.returncode != 0:
                raise Exception(
                    f"LibreOffice conversion failed:\n"
                    f"STDOUT: {process.stdout}\n"
                    f"STDERR: {process.stderr}"
                )

            pdf_path = os.path.join(
                tmpdir,
                "input.pdf"
            )

            if not os.path.exists(pdf_path):
                raise Exception(
                    "PDF file not generated"
                )

            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

        self.env['ir.attachment'].sudo().create({
            'name': cached_name,
            'datas': base64.b64encode(pdf_data),
            'mimetype': 'application/pdf',
            'type': 'binary',
        })

        return pdf_data

    @api.model
    def cron_generate_docx_pptx_previews(self, batch_size=5):

        mimetypes = [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ]

        attachments = self.search([
            ('mimetype', 'in', mimetypes),
            ('type', '=', 'binary'),
            ('name', 'not like', 'cache_%')
        ], limit=batch_size)

        for attachment in attachments:

            try:
                if not attachment.datas:
                    continue

                ext = (
                    'docx'
                    if attachment.mimetype.endswith(
                        'wordprocessingml.document'
                    )
                    else 'pptx'
                )

                attachment._convert_to_pdf_with_cache(ext)

            except Exception:
                pass