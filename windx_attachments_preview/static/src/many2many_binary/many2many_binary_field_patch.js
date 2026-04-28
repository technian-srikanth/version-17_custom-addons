/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Many2ManyBinaryField} from "@web/views/fields/many2many_binary/many2many_binary_field";
import {useService} from "@web/core/utils/hooks";
import {useState, onWillStart} from "@odoo/owl";


export class Many2ManyBinaryFieldPreview extends Many2ManyBinaryField {

    setup() {
        super.setup(...arguments);

        this.messaging = useService("messaging");
        this.state = useState({
            attachments: [],
        });

        onWillStart(() => {
            this.getAttachments();
        });
    }

    async getAttachments() {
        try {
            if (!this.props.value || !this.props.value.records) {
                this.state.attachments = [];
                return;
            }
            console.log("outside");
            const messaging = await this.messaging.get();

            const attachments = this.props.value.records.map((record) => {
                console.log("inside");
                const attachment = messaging.models["Attachment"].insert({
                    id: record.resId,
                    name: record.data.name,
                    filename: record.data.datas_fname || record.data.name,
                    mimetype: record.data.mimetype,
                    url: `/web/content/${record.resId}?download=false`,
                    resModel: this.props.record.resModel,
                    resId: this.props.record.resId,
                });
                console.log("attachment", attachment);
                return {
                    id: record.resId,
                    attachment: attachment,
                };
            });

            this.state.attachments = attachments;

        } catch (e) {
            console.error("Attachment error:", e);
            this.state.attachments = [];
        }
    }

    getAttachmentById(id) {
        const found = this.state.attachments.find(a => a.id === id);
        console.log("getting");
        return found ? found.attachment : false;
    }

    async previewAttachment(attachment) {
        if (!attachment || !attachment.isViewable) return;

        const messaging = await this.messaging.get();
        console.log("attach");
        const attachmentList = messaging.models["AttachmentList"].insert({
            attachments: [attachment],
            selectedAttachment: attachment,
        });

        messaging.models["Dialog"].insert({
            attachmentListOwnerAsAttachmentView: attachmentList,
        });
    }
}

registry.category("fields").add("many2many_preview_attachment", Many2ManyBinaryFieldPreview);