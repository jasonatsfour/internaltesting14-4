# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class VendorPricelistCreate(models.TransientModel):
    """
    This wizard will create vendors by using details feched from Octopart
    """
    _name = 'vendor.pricelist.create'
    _description = 'Vendor PricelistCreate'

    def create_vendors_pricelist(self):
        partner_obj = self.env['res.partner']
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        available_vendor_uid = partner_obj.search(
            [('octopart_id', '!=', '')]).mapped('octopart_id')
        sku_fail_list = []
        sku_done_list = []
        already_avail = []
        for detail in self.env['octopart.seller.detail'].browse(active_ids):
            if detail.product_tmpl_id:
                avail_vendor = partner_obj.search(
                    [('octopart_id', '=', detail.uid)], limit=1)
                vendor_by_name = partner_obj.search(
                    [('name', '=', detail.name),
                     ('octopart_id', '=', False)], limit=1)
                if avail_vendor or vendor_by_name:
                    if vendor_by_name:
                        vendor_by_name.octopart = True
                        vendor_by_name.octopart_id = detail.uid
                    self.create_pricelist(
                        detail, avail_vendor, vendor_by_name)
                    sku_done_list.append([detail.name, detail.sku])
                    continue
                if detail.uid not in available_vendor_uid:
                    vendor = partner_obj.create({
                        'name': detail.name,
                        'supplier_rank': 1,
                        'octopart': True,
                        'octopart_id': detail.uid
                    })
                    if detail.product_tmpl_id:
                        self.create_pricelist(detail, vendor, vendor)
                        sku_done_list.append([detail.name, detail.sku])
            else:
                sku_fail_list.append(detail.sku)
        self._cr.commit()
        message = ''
        if sku_fail_list:
            fail_detail = ''
            for fail_sku in sku_fail_list:
                fail_detail += 'SKU: %s \n' % (fail_sku)
            if fail_detail:
                message += \
                    'Pricelists are not created for following SKU: ' \
                    '\n %s \n ' % (fail_detail)
        if sku_done_list:
            done_detail = ''
            for sku in sku_done_list:
                done_detail += 'Vendor: %s \n SKU: %s \n' % (sku[0],sku[1])
            if done_detail:
                message += \
                    "Pricelists created successfully for following SKU: \n " \
                    "%s \n" % (done_detail)
        if already_avail:
            avail_detail = ''
            for sku in already_avail:
                avail_detail += 'Vendor: %s \n SKU: %s \n' % (sku[0],sku[1])
            if avail_detail:
                message += "Pricelists already available for following SKU: " \
                           "\n %s" % (avail_detail)
        if message:
            raise UserError(_(message))

    def create_pricelist(self, detail, avail_vendor, vendor_by_name):
        try:
            pricelist_ids = self.env['product.supplierinfo']
            detail_read = detail.read(['qty_1', 'qty_10', 'qty_100', 'qty_1000', 'qty_10000'])[0]
            multiple_quantities = detail.read([list(filter(lambda x: float(detail_read[x]) != 0.0, detail_read))])[0]
            del multiple_quantities['id']
            for qty in multiple_quantities:
                existing_pricelist = pricelist_ids.search([('octopart_pricelist_id', '=', detail.octopart_pricelist_id), ('min_qty', '=', float(qty.split('_')[1]))])
                if not existing_pricelist:
                    pricelist_ids |= pricelist_ids.create({
                        'product_tmpl_id': detail.product_tmpl_id.id,
                        'product_name':
                            detail.description or detail.product_tmpl_id.name,
                        'product_code': detail.sku,
                        'name':
                            avail_vendor and avail_vendor.id or
                            vendor_by_name and vendor_by_name.id,
                        'min_qty': qty.split('_')[1],
                        'octopart_price': multiple_quantities[qty] or 0,
                        'octopart_pricelist_id': detail.octopart_pricelist_id,
                    })
                else:
                    existing_pricelist.write({'min_qty': qty.split('_')[1], 'octopart_price': multiple_quantities[qty] or 0,})
            pricelist_ids.update_octopart_price()
        except Exception:
            pass
        return pricelist_ids
