/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {Component, xml, markup} from "@odoo/owl";

export class CsvPreviewContent extends Component {
    static components = {Dialog};
}

CsvPreviewContent.template = xml`
    <Dialog title="props.title" size="'fullscreen'" technical="false">

        <div class="d-flex flex-column h-100 bg-800">

            <div class="flex-grow-1 overflow-auto p-4 bg-view shadow-lg m-4"
                 style="border-radius:4px;">

                <t t-out="props.html"/>

            </div>

        </div>

        <t t-set-slot="footer">

            <button class="btn btn-primary"
                t-on-click="() => props.close()">
                Close Preview
            </button>

        </t>

    </Dialog>
`;


document.addEventListener("click", async function (ev) {

    const card = ev.target.closest(".o-mail-AttachmentCard");
    if (!card) return;

    console.log(card.innerHTML);

    const nameEl = card.querySelector(".text-truncate");
    const filename = nameEl ? nameEl.innerText.trim() : "";

    if (!filename.toLowerCase().endsWith(".csv")) return;

    ev.preventDefault();
    ev.stopPropagation();

    const btn = card.querySelector('button[title="Download"]');
    const downloadUrl = btn.getAttribute('data-download-url');

    const attachmentId = new URL(downloadUrl, window.location.origin)
        .pathname.split('/')
        .pop();

    console.log(attachmentId)

    const response = await fetch(`/csv/preview/${attachmentId}`);
    const data = await response.json();

    let table = "<table class='table table-sm table-striped border'>";

    data.rows.forEach((row, index) => {
        table += "<tr>";

        row.forEach(cell => {
            table += index === 0
                ? `<th class="bg-200">${cell}</th>`
                : `<td>${cell}</td>`;
        });

        table += "</tr>";
    });

    table += "</table>";

    const dialogService = owl.Component.env.services.dialog;

    dialogService.add(CsvPreviewContent, {
        title: filename,
        html: markup(table),
    });

});