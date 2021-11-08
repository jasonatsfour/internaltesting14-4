# -*- coding: utf-8 -*-
#Change to force Odoo.sh update. Force more updates
from odoo import api, models, fields


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
            self.set_octopart_product_status()
    
    def set_octopart_product_status(self):
        for line in self:
            if line.product_id:
                if not line.product_id.mpn and \
                        not line.product_id.sku:
                    line.octopart_price_fetched = 'not_octopart'
                    line.octopart_status = 'Not Octopart Product'
                if not line.order_id.partner_id.octopart:
                    line.octopart_price_fetched = 'not_applicable'
                    line.octopart_status = 'Not Applicable'
                else:
                    flag = False
                    try:
                        octopart_result = line.update_octopart_price()
                        if type(octopart_result) == type({}):
                            price = octopart_result.get('price')
                            line.octopart_price_fetched = 'found'
                            line.octopart_status = 'Found'
                            line.price_unit = float(price)
                        elif not octopart_result:
                            flag = True
                            supplierinfo = self.env['product.supplierinfo']
                            pricelist_ids = supplierinfo.search(
                                [('name', '=', line.order_id.partner_id.id),
                                 ('product_tmpl_id', '=',
                                  line.product_id.product_tmpl_id.id)],
                                limit=1)
                            vendor_pricelist = None
                            for pricelist in pricelist_ids:
                                vendor_pricelist = pricelist
                                if pricelist.min_qty == line.product_qty:
                                    vendor_pricelist = pricelist
                                    break
                            if vendor_pricelist:
                                price = \
                                    vendor_pricelist.octopart_price or \
                                    vendor_pricelist.price
                                line.price_unit = float(price)
                                flag = False
                                if not line.product_id.mpn and not \
                                        vendor_pricelist.product_code:
                                    line.octopart_price_fetched = \
                                        'not_octopart'
                                    line.octopart_status = \
                                        'Not Octopart Product'
                                else:
                                    line.octopart_price_fetched = 'found'
                                    line.octopart_status = 'Found'
                    except Exception:
                        flag = True
                    if flag:
                        line.octopart_price_fetched = 'not_found'
                        line.octopart_status = 'Not Found'
                        line.price_unit = 0.0

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        self.set_octopart_product_status()
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
