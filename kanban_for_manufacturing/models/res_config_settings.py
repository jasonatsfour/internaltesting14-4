# -*- coding: utf-8 -*-
# © 2018-Today Aktiv Software (http://aktivsoftware.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Class inherit for adding some configuration."""

    _inherit = 'res.config.settings'
    
    @api.model
    def default_get(self, fields):
        """Function call for get default value."""
        res = super(ResConfigSettings, self).default_get(fields)
        for data in self.search([]):
            res.update({
                'internal_transfer_kanban_id':
                data.internal_transfer_kanban_id.id,
                'manufacturing_route_kanban_id':
                data.manufacturing_route_kanban_id.id
            })
        return res

    manufacturing_route_kanban_id = fields.Many2one(
        'procurement.rule',
        "Manufacturing Route for Kanban")
    internal_transfer_kanban_id = fields.Many2one(
        'stock.picking.type',
        "Internal Transfer Type for Kanban")

