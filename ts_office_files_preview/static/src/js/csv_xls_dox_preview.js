/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {Component, xml} from "@odoo/owl";

export class DocumentPreview extends Component {

    static components = {Dialog};

    downloadFile() {

        const url = `/web/content/${this.props.attachmentId}?download=true`;

        const a = document.createElement("a");
        a.href = url;
        a.download = this.props.title;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

}

DocumentPreview.template = xml`
<Dialog size="'fullscreen'" technical="false"
    class="'o_doc_preview_dialog'"
    contentClass="'o_full_screen_preview'">

<t t-set-slot="header">
    <div class="header">
        <h5 class="mb-0 text-truncate text-white" t-esc="props.title"/>
    
        <div class="section-2">
            <button class="download-btn btn btn-secondary" t-on-click="downloadFile">
                <i class="fa fa-download"/> Download
            </button>
    
            <button class="btn-close bg-white p-1 mr-2"
                    t-on-click="props.close"/>
        </div>
    
    </div>
</t>

<div class="o_preview_container d-flex flex-column justify-content-center fixed bottom-0 m-0 p-0">
    <div id="doc_viewer"
         class="o_doc_viewer flex-grow-1 overflow-auto p-2">
        Loading preview...
    </div>
</div>
<t t-set-slot="footer">
.
</t>
</Dialog>
`;


document.addEventListener("click", async function (ev) {

    const card = ev.target.closest(".o-mail-AttachmentCard");
    if (!card) return;

    const nameEl = card.querySelector(".text-truncate");
    const filename = nameEl ? nameEl.innerText.trim() : "";

    if (![".csv", ".xlsx", ".docx"]
        .some(ext => filename.toLowerCase().endsWith(ext))) {
        return;
    }

    ev.preventDefault();
    ev.stopPropagation();

    const btn = card.querySelector('button[title="Download"]');
    const downloadUrl = btn.getAttribute("data-download-url");

    const attachmentId = new URL(downloadUrl, window.location.origin)
        .pathname
        .split("/")
        .pop();

    const dialogService = owl.Component.env.services.dialog;

    dialogService.add(DocumentPreview, {
        title: filename,
        attachmentId: attachmentId,
    });


    setTimeout(async () => {

        const viewer = document.getElementById("doc_viewer");
        const fileUrl = `/web/content/${attachmentId}`;

        viewer.innerHTML = "Loading preview...";

        if (filename.endsWith(".csv") || filename.endsWith(".xlsx")) {

            const response = await fetch(`/csv/preview/${attachmentId}`);
            const data = await response.json();

            let table = "<table class='table table-striped table-bordered bg-white'>";

            data.rows.forEach((row, index) => {

                table += "<tr>";

                row.forEach(cell => {

                    table += index === 0
                        ? `<th>${cell}</th>`
                        : `<td>${cell}</td>`;

                });

                table += "</tr>";

            });

            table += "</table>";

            viewer.innerHTML = table;
        }


        /* DOCX */

        else if (filename.endsWith(".docx")) {

            const file = await fetch(fileUrl).then(r => r.arrayBuffer());

            viewer.innerHTML = "";

            docx.renderAsync(file, viewer);

        }

    }, 200);

});


document.addEventListener("mouseover", function (ev) {

    const card = ev.target.closest(".o-mail-AttachmentCard");
    if (!card) return;

    if (!card.dataset.cursorSet) {
        card.style.cursor = "zoom-in";
        card.dataset.cursorSet = "true";
    }

});