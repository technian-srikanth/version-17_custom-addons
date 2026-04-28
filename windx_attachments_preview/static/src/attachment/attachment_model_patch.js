/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Attachment } from "@mail/core/common/attachment_model";

const descriptor = Object.getOwnPropertyDescriptor(
    Attachment.prototype,
    "isViewable"
);

const originalIsViewable = descriptor?.get;

patch(Attachment.prototype, {

    get fileName() {
        return (this.name || this.filename || "").toLowerCase();
    },

    get isDocx() {
        return this.fileName.endsWith(".docx");
    },

    get isPPTX() {
        return this.fileName.endsWith(".pptx");
    },

    get isXLSX() {
        return this.fileName.endsWith(".xlsx");
    },

    get isOfficeFile() {
        return this.isDocx || this.isPPTX || this.isXLSX;
    },

    get isViewable() {
        if (this.isOfficeFile) {
            return true;
        }
        return originalIsViewable ? originalIsViewable.call(this) : false;
    },
});