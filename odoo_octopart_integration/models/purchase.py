# -*- coding: utf-8 -*-
#Change to force Odoo.sh update. Force more updates
from odoo import api, models, fields


def downgrade_qty(qty):
    """
    :param qty: price is not available for this qty
    :return: downgraded qty and if not than return False
    """
    if 1 <= qty < 10:
        return False
    elif 10 <= qty < 100:
        return 1
    elif 100 <= qty < 1000:
        return 10
    elif 1000 <= qty < 10000:
        return 100
    elif qty >= 10000:
        return 1000
    return 0


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    manual_override = fields.Boolean(string='Manual Override',
                                     compute='is_manual_override')
    octopart_product = fields.Boolean(string='Manual Override',
                                      compute='is_octopart_product')
    octopart_price_fetched = fields.Selection(
        [('not_applicable', 'Not Applicable'), ('not_found', 'Not Found'),
         ('not_octopart', 'Not Octopart Product'), ('found', 'Updated'), ],
        string='Octopart Price')
    octopart_status = fields.Char(string='Octopart Status')
    pricelist_id = fields.Many2one('product.supplierinfo', 'Product Pricelist Id')

    @api.model
    def default_get(self, fields):
        rec = super(PurchaseOrderLine, self).default_get(fields)
        rec.update({'product_qty': 1})
        return rec

    @api.depends('product_id')
    def is_octopart_product(self):
        for line in self:
            line.octopart_product = False
            if line.product_id.sku or line.product_id.mpn:
                line.octopart_product = True

    @api.depends('product_id', 'product_qty', 'order_id.partner_id')
    def is_manual_override(self):
        supplierinfo = self.env['product.supplierinfo']
        for line in self:
            vendor_pricelist = supplierinfo.search(
                [('name', '=', line.order_id.partner_id.id),
                 ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)],
                limit=1)
            if not vendor_pricelist:
                line.manual_override = False
            else:
                line.manual_override = vendor_pricelist and \
                                       vendor_pricelist.manual_override
            # self.set_octopart_product_status()

    def set_octopart_product_status(self,price=0):
        for line in self:
            line.octopart_price_fetched = 'not_octopart'
            line.octopart_status = 'Not Octopart Product'
            if not line.order_id.partner_id.octopart:
                line.octopart_price_fetched = 'not_applicable'
                line.octopart_status = 'Not Applicable'
            if price > 0:
                    line.octopart_price_fetched = 'found'
                    line.octopart_status = 'Found'

    def get_oct_price(self, octopart, qty):
        price = octopart.fetch_octopart_api_details(self.partner_id, self.product_id, qty, self.pricelist_id,
                                                    product_code=self.product_id.mpn)
        if not price:
            qty = downgrade_qty(qty)
            return qty and self.get_oct_price(octopart, qty) or 0
        else:
            price = price.get('price', 0)
            return price

    def get_octopart_price_by_qty(self):
        """ Get Octopart Price Unit for the selected product and qty"""
        octopart = self.env['octopart.configuration'].search(
            [('active', '=', True)], limit=1, order='id desc')
        price = 0
        qty = 1 if 1 <= self.product_qty < 10 else 10 if 10 <= self.product_qty < 100 else 100 if 100 <= self.product_qty < 1000 else 1000 if 1000 <= self.product_qty < 10000 else 10000 if self.product_qty >= 10000 else 0
        if self.partner_id and self.pricelist_id and self.product_id:
            price = self.get_oct_price(octopart, qty)
        return price

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        price = self.get_octopart_price_by_qty()
        if price > 0:
            self.price_unit = price
        self.set_octopart_product_status(price=price)
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        pricelist_model = self.env['product.supplierinfo']
        if self.name and self.product_id:
            product_code = self.name.split(']')[0][1:]
            pricelist_id = pricelist_model.sudo().search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('product_code', '=', product_code),
            ], limit=1)
            self.pricelist_id = pricelist_id and pricelist_id.id or pricelist_model
        return res

    def update_octopart_price(self):
        supplierinfo = self.env['product.supplierinfo']
        for obj in self:
            pricelist_ids = supplierinfo.search(
                [('name', '=', obj.order_id.partner_id.id),
                 ('product_tmpl_id', '=',
                  obj.product_id.product_tmpl_id.id)])
            vendor_pricelist = None
            product_code = ''
            for pricelist in pricelist_ids:
                product_code = pricelist.product_code
                if pricelist.min_qty == obj.product_qty:
                    vendor_pricelist = pricelist
                    break
            if not product_code:
                return False
            if not vendor_pricelist:
                octopart = self.env['octopart.configuration'].search(
                    [('active', '=', True)], limit=1, order='id desc')
                return octopart.fetch_octopart_api_details(
                    obj.order_id.partner_id, obj.product_id.product_tmpl_id,
                    obj.product_qty, vendor_pricelist, product_code)
            else:
                return {'price': vendor_pricelist.octopart_price}
            return vendor_pricelist.update_details_from_octopart()

    @api.model
    def create(self, vals):
        pol_rec = super(PurchaseOrderLine, self).create(vals)
        supplierinfo = self.env['product.supplierinfo']
        pricelist_ids = supplierinfo.search(
            [('name', '=', pol_rec.order_id.partner_id.id),
             ('product_tmpl_id', '=',
              pol_rec.product_id.product_tmpl_id.id)],
            limit=1)
        vendor_pricelist = None
        for pricelist in pricelist_ids:
            vendor_pricelist = pricelist
            if pricelist.min_qty == pol_rec.product_qty:
                vendor_pricelist = pricelist
                break
        if vendor_pricelist:
            price = \
                vendor_pricelist.octopart_price or \
                vendor_pricelist.price
            pol_rec.price_unit = price
        pol_rec.set_octopart_product_status()
        return pol_rec
