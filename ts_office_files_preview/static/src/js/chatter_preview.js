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

        else if (filename.toLowerCase().endsWith(".docx")) {

            const viewer = document.getElementById("doc_viewer");
            viewer.innerHTML = "Loading preview...";

            try {
                const response = await fetch(`/web/content/${attachmentId}`);
                const arrayBuffer = await response.arrayBuffer();

                const result = await mammoth.convertToHtml({arrayBuffer});

                viewer.innerHTML = `
            <div class="pdf-viewer">
                <div class="doc-content">
                    ${result.value}
                </div>
            </div>
        `;

                // wait for DOM render
                setTimeout(async () => {

                    // wait for images
                    const images = viewer.querySelectorAll("img");
                    await Promise.all([...images].map(img => {
                        if (img.complete) return Promise.resolve();
                        return new Promise(res => {
                            img.onload = res;
                            img.onerror = res;
                        });
                    }));

                    splitIntoPdfPages();

                }, 100);

            } catch (err) {
                console.error("DOCX preview failed:", err);
                viewer.innerHTML = "❌ Failed to render document";
            }
        } else if (filename.toLowerCase().endsWith(".pptx")) {

            const viewer = document.getElementById("doc_viewer");
            if (!viewer) return;

            viewer.innerHTML = `
                <div id="pptx_container" style="width:100%; height:100%; overflow:auto;"></div>
            `;

            const fileUrl = `/web/content/${attachmentId}`;

            try {
                console.log("Initializing SlideJS...");

                window.slideJS = window.createSlideJS();

                const response = await fetch(fileUrl);
                const fileBlob = await response.blob();

                console.log("Parsing PPTX...");


                window.slideParser(fileBlob, () => {

                    console.log("Rendering slides...");

                    const container = document.getElementById("pptx_container");
                    container.style.display = "flex";
                    container.style.justifyContent = "center";
                    container.style.alignItems = "center";
                    container.style.height = "80%";

                    window.slideAfterRender(container, () => {
                        console.log("Render complete");
                    });

                }, (error) => {
                    console.error("SlideJS parse error:", error);
                    viewer.innerHTML = "❌ Failed to parse PPTX";
                });

            } catch (err) {
                console.error("PPTX load failed:", err);
                viewer.innerHTML = "❌ Failed to load PPTX";
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
//
// // Add 'async' to your function
// async function splitDocxPages(container) {
//     const PAGE_HEIGHT = 939;
//     const article = container.querySelector("article");
//     if (!article) return;
//
//     // Ensure all images are loaded before measuring
//     const images = article.querySelectorAll('img');
//     await Promise.all([...images].map(img => {
//         if (img.complete) return Promise.resolve();
//         return new Promise(resolve => {
//             img.onload = resolve;
//             img.onerror = resolve;
//         });
//     }));
//
//     const nodes = [...article.children];
//     let page = container.querySelector("section.docx");
//     let currentHeight = 0;
//     const pages = [page];
//
//     nodes.forEach(node => {
//         const nodeHeight = node.getBoundingClientRect().height; // Use more precise measurement
//
//         if (currentHeight + nodeHeight > PAGE_HEIGHT && currentHeight > 0) {
//             const newPage = document.createElement("section");
//             newPage.className = "docx";
//             const newArticle = document.createElement("article");
//             newPage.appendChild(newArticle);
//             container.appendChild(newPage);
//
//             page = newPage;
//             pages.push(page);
//             currentHeight = 0;
//         }
//
//         page.querySelector("article").appendChild(node);
//         currentHeight += nodeHeight;
//     });
//
//     // Now totalPages will be correct (e.g., 2)
//     pages.forEach((p, index) => {
//         // Remove existing footers if any to prevent duplicates
//         const existing = p.querySelector(".docx-page-number");
//         if (existing) existing.remove();
//
//         const footer = document.createElement("div");
//         footer.className = "docx-page-number";
//         footer.textContent = `Page ${index + 1} of ${pages.length}`;
//         p.appendChild(footer);  
//     });
// }


function splitIntoPdfPages() {

    const content = document.querySelector(".doc-content");
    const viewer = document.querySelector(".pdf-viewer");

    if (!content || !viewer) return;

    const PAGE_HEIGHT = 1122; // A4 height
    const nodes = [...content.children];

    viewer.innerHTML = "";

    let page = createPage();
    viewer.appendChild(page);

    let currentHeight = 0;

    nodes.forEach(node => {

        page.appendChild(node);

        const height = node.getBoundingClientRect().height;

        if (currentHeight + height > PAGE_HEIGHT && currentHeight > 0) {

            page.removeChild(node);

            page = createPage();
            viewer.appendChild(page);

            page.appendChild(node);
            currentHeight = height;

        } else {
            currentHeight += height;
        }
    });

    addPageNumbers();
}

function createPage() {
    const page = document.createElement("div");
    page.className = "pdf-page";

    const inner = document.createElement("div");
    inner.className = "pdf-page-inner";

    page.appendChild(inner);
    return page;
}

function addPageNumbers() {
    const pages = document.querySelectorAll(".pdf-page");

    pages.forEach((page, index) => {
        const footer = document.createElement("div");
        footer.className = "pdf-footer";
        footer.innerText = `Page ${index + 1} of ${pages.length}`;
        page.appendChild(footer);
    });
}