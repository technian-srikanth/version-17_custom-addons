/** @odoo-module **/

import { AttachmentView } from "@mail/core/common/attachment_view";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(AttachmentView.prototype, {

    setup() {
        super.setup();

        this.viewerMsOfficeRef = { el: null };
        this.instancePreviewOffice = null;
        this._isRendering = false;

        console.log("PATCH APPLIED TO AttachmentView");
        console.log("Props:", this.props);

        onMounted(() => {
            setTimeout(() => {
                this.injectOfficeViewer();
            }, 0);
        });
    },

    injectOfficeViewer() {
        const attachment = this.props?.attachment;

        console.log("attachment", attachment);

        if (!attachment) return;

        if (!attachment.isDocx && !attachment.isXLSX && !attachment.isPPTX) {
            return;
        }

        const container = this.el?.querySelector(".o_AttachmentViewer_main");
        console.log("Container:", container);

        if (!container) return;

        if (container.querySelector(".o_AttachmentViewer_view_ms_office")) {
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = "o_AttachmentViewer_view_ms_office w-100 h-100";

        const inner = document.createElement("div");
        inner.className = "w-100 h-100";

        wrapper.appendChild(inner);
        container.appendChild(wrapper);

        this.viewerMsOfficeRef.el = inner;

        this.previewMsOffice(inner);
    },

    async previewMsOffice(rootElement) {
        if (this._isRendering) return;
        this._isRendering = true;

        const attachment = this.props?.attachment;

        if (!attachment?.isOfficeFile) {
            this._isRendering = false;
            return;
        }

        if (attachment.isPPTX && typeof window.createSlideJS !== "function") {
            console.warn("SlideJS not loaded ❌");
            this._isRendering = false;
            return;
        }

        this.instancePreviewOffice = window.createSlideJS();

        const file = await this.getFileFromUrl(
            `/web/content/${attachment.id}?download=false`,
            attachment.name
        );

        console.log("file", file);

        this.instancePreviewOffice.parse(
            file,
            () => {
                window.slideAfterRender?.(rootElement, () => {}, 0);
                this._isRendering = false;
            },
            (e) => {
                console.error("SlideJS error:", e);
                this._isRendering = false;
            }
        );
    },

    async getFileFromUrl(url, name, defaultType = "application/octet-stream") {
        const res = await fetch(url);
        const blob = await res.blob();
        return new File([blob], name, { type: blob.type || defaultType });
    },
});