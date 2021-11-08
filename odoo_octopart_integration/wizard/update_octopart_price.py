# -*- coding: utf-8 -*-
from odoo import api, models


class UpdateOctopartVendorPrice(models.TransientModel):
    """
    This wizard will update vendor's octopart price from Octopart
    """

    _name = "update.octopart.price"
    _description = "Update Octopart Vendor Price"

    def update_price(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['product.supplierinfo'].browse(active_ids):
            record.update_details_from_octopart()
        return {'type': 'ir.actions.act_window_close'}
