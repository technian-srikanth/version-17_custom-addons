from odoo import http
from odoo.http import request
import base64
import csv
import io
import json
import openpyxl
# from pptx import Presentation


class AttachmentPreviewController(http.Controller):

    @http.route('/csv/preview/<int:attachment_id>', auth='user', type='http')
    def preview_attachment(self, attachment_id):

        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)

        if not attachment.exists() or not attachment.datas:
            return self._json_response({"rows": []})

        file_data = base64.b64decode(attachment.datas)
        filename = attachment.name.lower()

        rows = []

        try:
            file_input = io.BytesIO(file_data)

            if filename.endswith(".xlsx"):

                wb = openpyxl.load_workbook(
                    file_input,
                    read_only=True,
                    data_only=True
                )

                sheet = wb.active

                for row in sheet.iter_rows(values_only=True):
                    rows.append([
                        str(cell) if cell is not None else ""
                        for cell in row
                    ])

            # CSV preview
            elif filename.endswith(".csv"):

                file_content = file_data.decode("utf-8", errors="ignore")
                csv_file = io.StringIO(file_content)

                try:
                    dialect = csv.Sniffer().sniff(file_content[:1024]) if file_content else csv.excel
                    reader = csv.reader(csv_file, dialect)
                except Exception:
                    csv_file.seek(0)
                    reader = csv.reader(csv_file)

                rows = list(reader)


        except Exception as e:
            return self._json_response({"error": str(e)})

        return self._json_response({"rows": rows})

    def _json_response(self, data):
        return request.make_response(
            json.dumps(data),
            headers=[("Content-Type", "application/json")]
        )
