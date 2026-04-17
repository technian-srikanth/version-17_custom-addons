/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {renderToMarkup} from '@web/core/utils/render';
import {markup} from "@odoo/owl";

const greenBullet = markup(`<span class="o_status d-inline-block o_status_green"></span>`);
const orangeBullet = markup(`<span class="o_status d-inline-block text-warning"></span>`);
const star = markup(`<a style="color: gold;" class="fa fa-star"></a>`);
const clock = markup(`<a class="fa fa-clock-o"></a>`);

const projectExamples = registry.category("kanban_examples").get("project");
projectExamples.examples.unshift({
        name: _t('Mobile App Development'),
        columns: [_t('Backlog'), _t('Design'), _t('Development'), _t('QA')],
        foldedColumns: [_t('Released')],
        get description() {
            return renderToMarkup("project.example.generic");
        },
        bullets: [greenBullet, orangeBullet, star, clock],
    },
    {
        name: _t('WEB Development'),
        columns: [_t('Design'), _t('Development'), _t('QA')],
        foldedColumns: [_t('Released')],
        get description() {
            return renderToMarkup("project.example.generic");
        },
        bullets: [greenBullet, orangeBullet, star, clock],
    },
);
