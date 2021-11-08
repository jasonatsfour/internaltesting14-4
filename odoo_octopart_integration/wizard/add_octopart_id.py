# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AddOctopartId(models.TransientModel):

    _name = 'add.octopart.id'
    _description = 'Add Octopart Id'

    name = fields.Char(string='Distributor')
    sku = fields.Char(string='SKU')
    uid = fields.Char(string='Octopart Id')
    stock = fields.Char(string='Stock')
    min_qty = fields.Char(string='MOQ')
    pkg = fields.Char(string='PKG')
    currency_id = fields.Many2one('res.currency', string='Currency')
    qty_1 = fields.Char(string='1')
    qty_10 = fields.Char(string='10')
    qty_100 = fields.Char(string='100')
    qty_1000 = fields.Char(string='1,000')
    qty_10000 = fields.Char(string='10,000')
    last_updated = fields.Datetime(string='Updated')
    product_tmpl_id = fields.Many2one('product.template', string='Product')
    description = fields.Char(string='Description')
    wizard_id = fields.Many2one('add.octopart.wizard', string='WizardId')

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "[%s] %s [MOQ: %s]" % (
                record.sku, record.name, record.min_qty)))
        return result


class AddOctopartwizard(models.TransientModel):

    _name = 'add.octopart.wizard'
    _description = 'Add Octopart Wizard'

    octopart_id = fields.Many2one('add.octopart.id', string='Octopart Details')

    def set_vendor_octopart_id(self):
        for object in self:
            active_id = self.env.context.get('active_id')
            pricelist = self.env['product.supplierinfo'].browse(active_id)
            if object.octopart_id and active_id:
                pricelist.name.octopart = True
                pricelist.min_qty = object.octopart_id.min_qty
                pricelist.name.octopart_id = object.octopart_id.uid
            pricelist.update_octopart_price()
