/* @odoo-module */

import { registerPatch } from '@mail/model/model_core';
import { attr } from '@mail/model/model_field';
// dummy import to ensure mail Messaging patches are loaded beforehand
import '@mail/models/attachment_viewer_viewable';

registerPatch({
    name: 'AttachmentViewerViewable',
    fields: {
        /**
         * States id the attachment is an Doc.
         */
        isDoc: attr({
            compute() {
                return this.attachmentOwner.isDoc;
            },
        }),
        /**
         * States id the attachment is an Docx.
         */
        isDocx: attr({
            compute() {
                return this.attachmentOwner.isDocx;
            },
        }),
        /**
         * States id the attachment is an ppt.
         */
        isPPT: attr({
            compute() {
                return this.attachmentOwner.isPPT;
            },
        }),
        /**
         * States id the attachment is an pptx.
         */
        isPPTX: attr({
            compute() {
                return this.attachmentOwner.isPPTX;
            },
        }),
        /**
         * States id the attachment is an xlsx.
         */
        isXLS: attr({
            compute() {
                return this.attachmentOwner.isXLS;
            },
        }),
        /**
         * States id the attachment is an xlsx.
         */
        isXLSX: attr({
            compute() {
                return this.attachmentOwner.isXLSX;
            },
        }),
        isOfficeFile: attr({
            compute() {
                return this.attachmentOwner.isOfficeFile;
            },
        }),
    },
});
