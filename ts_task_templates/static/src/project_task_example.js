/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { renderToMarkup } from '@web/core/utils/render';

const projectExamples = registry.category("kanban_examples").get("project");

projectExamples.examples.push({
    name: _t('Mobile App Development'),
    columns: [_t('Backlog'), _t('Design'), _t('Development'), _t('QA')],
    foldedColumns: [_t('Released')],
    get description() {
        return renderToMarkup("project.example.generic");
    },
});
