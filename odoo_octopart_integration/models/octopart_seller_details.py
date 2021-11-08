# -*- coding: utf-8 -*-
from odoo import fields, models


class OctopartSellerDetail(models.Model):
    """
    This object will store seller's details from Octopart
    """

    _name = 'octopart.seller.detail'
    _description = 'Octopart Seller Details'

    name = fields.Char(string='Distributor')
    sku = fields.Char(string='SKU')
    uid = fields.Char(string='Uid')
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
    octopart_pricelist_id = fields.Char("Octopart Pricelist ID")
