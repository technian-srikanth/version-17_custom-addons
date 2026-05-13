from odoo import models, api
import logging
import base64
import tempfile
import subprocess
import os
import platform
import shutil

_logger = logging.getLogger(__name__)

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
            IGNORED_LO_MESSAGES = (
                "Ignoring hdmx table",
                "Could not find platform independent libraries",
            )

            stderr = process.stderr.strip()

            if stderr and not any(msg in stderr for msg in IGNORED_LO_MESSAGES):
                _logger.error(
                    "LibreOffice STDERR: %s",
                    stderr
                )

            _logger.info(
                "LibreOffice Return Code: %s",
                process.returncode
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
        """
        Generate cached PDF previews
        for DOCX / PPTX attachments.
        """

        mimetypes = [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ]

        attachments = self.search([
            ('mimetype', 'in', mimetypes),
            ('type', '=', 'binary'),
            ('name', 'not like', 'cache_%')
        ], limit=batch_size)

        _logger.info(
            "DOCX/PPTX Preview Cron Started. Found %s attachments",
            len(attachments)
        )

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

                _logger.info(
                    "Preview generated for attachment ID %s (%s)",
                    attachment.id,
                    ext
                )

            except Exception as e:

                _logger.exception(
                    "Failed to generate preview "
                    "for attachment ID %s: %s",
                    attachment.id,
                    str(e)
                )

        _logger.info(
            "DOCX/PPTX Preview Cron Completed"
        )
