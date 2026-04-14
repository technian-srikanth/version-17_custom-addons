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

    onWillUnmount() {
        // cleanup ppt viewer
        const ppt = document.getElementById("pptx_viewer_container");
        if (ppt) {
            ppt.innerHTML = "";
        }

        // remove any leftover ppt navigation
        document.querySelectorAll(".pptxjs").forEach(el => el.remove());
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
            <button class="btn-close"
                    t-on-click="props.close"/>
        </div>
    </div>
</t>

<div class="o_preview_container d-flex flex-column justify-content-center fixed bottom-0 m-0 p-0">
    <div id="doc_viewer" class="o_doc_viewer flex-grow-1 overflow-auto">
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

    console.log("file", filename)

    if (![".csv", ".xlsx", ".docx", ".pptx"]
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

        if (filename.endsWith(".xlsx") || filename.endsWith(".csv")) {

            const response = await fetch(`/csv/preview/${attachmentId}`);
            const data = await response.json();

            console.log("data", data);

            viewer.innerHTML = "";
            viewer.style.height = "100%";

            const spreadsheet = x_spreadsheet(viewer, {
                mode: "read",
                showToolbar: false,
                showGrid: true,
                showContextmenu: false
            });
            const sheets = [];

            data.sheets.forEach(sheet => {

                const sheetRows = {
                    len: sheet.rows.length
                };

                sheet.rows.forEach((row, r) => {

                    const cells = {};

                    row.forEach((cell, c) => {
                        cells[c] = {
                            text: cell ? String(cell) : ""
                        };
                    });

                    sheetRows[r] = {cells};

                });

                sheets.push({
                    name: sheet.name,
                    rows: sheetRows
                });

            });

            spreadsheet.loadData(sheets);

            console.log("spreadsheet", spreadsheet);

        }
        /* DOCX */

        else if (filename.endsWith(".docx")) {

            const viewer = document.getElementById("doc_viewer");

            const file = await fetch(fileUrl).then(r => r.arrayBuffer());

            viewer.innerHTML = `<div class="docx-wrapper"></div>`;

            const container = viewer.querySelector(".docx-wrapper");

            console.log('container', container)

            await docx.renderAsync(file, container, null, {
                className: "docx",
                inWrapper: false,
                ignoreWidth: true,
                ignoreHeight: true
            });

            splitDocxPages(container);
        }

            // else if (filename.endsWith(".pptx")) {
            //     const viewer = document.getElementById("doc_viewer");
            //
            //     if (!viewer) {
            //         setTimeout(() => {
            //             const retryViewer = document.getElementById("doc_viewer");
            //             if (retryViewer) this._renderPPT(fileUrl);
            //         }, 150);
            //         return;
            //     }
            //
            //     viewer.innerHTML = `<div id="pptx_viewer_container" style="width:100%; height:100%;"></div>`;
            //
            //     setTimeout(() => {
            //         const container = $("#pptx_viewer_container");
            //         if (container.length > 0) {
            //             try {
            //                 container.pptxToHtml({
            //                     pptxFileUrl: fileUrl,
            //                     fileInputId: null,
            //                     slideMode: false,
            //                     keyBoardShortCut: true,
            //                     slideModeConfig: {
            //                         first: 1,
            //                         nav: true,
            //                         navDetails: true,
            //                         showSlideNumber: true,
            //                     }
            //                 });
            //             } catch (error) {
            //                 console.error("PPT preview failed:", error);
            //                 viewer.innerHTML = `
            //                     <div style="padding:20px">
            //                         Preview not supported for this PPT file.<br>
            //                         Please download to view.
            //                     </div>
            //                 `;
            //             }
            //         }
            //     }, 50);
        // }
        else if (filename.endsWith(".pptx")) {

            const viewer = document.getElementById("doc_viewer");
            if (!viewer) return;

            viewer.innerHTML = `<div id="pdf_container"></div>`;

            try {

                const response = await fetch(`/ppt/preview/${attachmentId}`);
                const pdfData = await response.arrayBuffer();

                // load PDF.js
                const pdfModule = await import("/ts_office_files_preview/static/lib/pdf.mjs");
                const pdfjsLib = pdfModule;

                pdfjsLib.GlobalWorkerOptions.workerSrc =
                    "/ts_office_files_preview/static/lib/pdf.worker.mjs";

                const loadingTask = pdfjsLib.getDocument({data: pdfData});
                const pdf = await loadingTask.promise;

                const container = document.getElementById("pdf_container");

                for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {

                    const page = await pdf.getPage(pageNum);

                    const viewport = page.getViewport({scale: 1 });

                    const canvas = document.createElement("canvas");
                    const ctx = canvas.getContext("2d");

                    canvas.height = viewport.height;
                    canvas.width = viewport.width;

                    canvas.style.display = "block";
                    canvas.style.margin = "10px auto";
                    container.appendChild(canvas);


                    const pageNumber = document.createElement("div");
                    pageNumber.innerText = `Page ${pageNum} of ${pdf.numPages}`;

                    pageNumber.style.textAlign = "right";
                    pageNumber.style.fontSize = "10px";
                    pageNumber.style.color = "#555";
                    pageNumber.style.marginBottom = "10px";

                    container.appendChild(pageNumber);

                    await page.render({
                        canvasContext: ctx,
                        viewport: viewport
                    }).promise;
                }

            } catch (err) {

                console.error("PDF preview failed:", err);

                viewer.innerHTML = `
            <div style="padding:10px">
                Preview not supported.<br>
                Please download the file.
            </div>
        `;
            }
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

function splitDocxPages(container) {

    const PAGE_HEIGHT = 1123; // A4 height
    const article = container.querySelector("article");

    if (!article) return;

    let page = container.querySelector("section.docx");
    let currentHeight = 0;

    const pages = [page];

    [...article.children].forEach(node => {

        const nodeHeight = node.offsetHeight;

        if (currentHeight + nodeHeight > PAGE_HEIGHT) {

            // create new page
            const newPage = document.createElement("section");
            newPage.className = "docx";

            const newArticle = document.createElement("article");
            newPage.appendChild(newArticle);

            container.appendChild(newPage);

            page = newPage;
            pages.push(page);

            currentHeight = 0;
        }

        page.querySelector("article").appendChild(node);
        currentHeight += nodeHeight;

    });

    // Add page numbers
    const totalPages = pages.length;

    pages.forEach((page, index) => {

        const footer = document.createElement("div");
        footer.className = "docx-page-number";
        footer.textContent = `Page ${index + 1} of ${totalPages}`;

        page.appendChild(footer);

    });

}