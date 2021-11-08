odoo.define('odoo_octopart_integration.basic_fields', function (require) {
    "use strict";
    var basic_fields = require('web.basic_fields');

    basic_fields.StateSelectionWidget.include({
        _prepareDropdownValues: function () {
        console.log(self)
            var self = this;
            var _data = [];
            var current_stage_id = self.recordData.stage_id && self.recordData.stage_id[0];
            var stage_data = {
                id: current_stage_id,
                legend_normal: this.recordData.legend_normal || undefined,
                legend_blocked : this.recordData.legend_blocked || undefined,
                legend_done: this.recordData.legend_done || undefined,
                legend_found: this.recordData.legend_found || undefined,
                legend_not_found: this.recordData.legend_not_found || undefined,
                legend_not_octopart: this.recordData.legend_not_octopart || undefined,
                legend_not_applicable: this.recordData.legend_not_applicable || undefined,
            };
            _.map(this.field.selection || [], function (selection_item) {
                var value = {
                    'name': selection_item[0],
                    'tooltip': selection_item[1],
                };
                if (selection_item[0] === 'normal') {
                    value.state_name = stage_data.legend_normal ? stage_data.legend_normal : selection_item[1];
                } else if (selection_item[0] === 'done') {
                    value.state_class = 'o_status_green';
                    value.state_name = stage_data.legend_normal ? stage_data.legend_normal : selection_item[1];
                }else if (selection_item[0] === 'found') {
                    self.$('.o_status').removeClass('o_status_red o_status_green o_status_not_octopart o_status_not_applicable');
                    value.state_class = 'o_status_green';
                    value.state_name = stage_data.legend_found ? stage_data.legend_found : selection_item[1];
                }else if (selection_item[0] === 'not_found') {
                    self.$('.o_status').removeClass('o_status_red o_status_green o_status_not_octopart o_status_not_applicable');
                    value.state_class = 'o_status_red';
                    value.state_name = stage_data.legend_not_found ? stage_data.legend_not_found : selection_item[1];
                }else if (selection_item[0] === 'not_octopart') {
                    self.$('.o_status').removeClass('o_status_red o_status_green o_status_not_octopart o_status_not_applicable');
                    value.state_class = 'o_status_not_octopart';
                    value.state_name = stage_data.legend_not_octopart ? stage_data.legend_not_octopart : selection_item[1];
                }else if (selection_item[0] === 'not_applicable') {
                    self.$('.o_status').removeClass('o_status_red o_status_green o_status_not_octopart o_status_not_applicable');
                    value.state_class = 'o_status_not_applicable';
                    value.state_name = stage_data.legend_not_applicable ? stage_data.legend_not_applicable : selection_item[1];
                }
                else {
                    value.state_class = 'o_status_red';
                    value.state_name = stage_data.legend_blocked ? stage_data.legend_blocked : selection_item[1];
                }
                _data.push(value);
            });
            return _data;
        },
    });
});