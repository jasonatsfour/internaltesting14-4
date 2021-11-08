# -*- coding: utf-8 -*-
from odoo import api, models


class ProductSupplierinfo(models.Model):
    """Class inherit for Add some functions."""

    _inherit = "product.supplierinfo"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Function call for search name + product code."""
        args = args or []
        domain = []
        if name:
            domain = [
                '|', ('name', operator, name),
                ('product_code', operator, name)]
        pricelist_recs = self.search(domain + args, limit=limit)
        return pricelist_recs.name_get()

    def name_get(self):
        """Display pricelist name + product_code."""
        res = []
        for pricelist_rec in self:
            name = pricelist_rec.name.name
            if pricelist_rec.product_name:
                name += ' - ' + pricelist_rec.product_name
            if pricelist_rec.product_code:
                name += ' - ' + pricelist_rec.product_code
            if pricelist_rec.price:
                name += ' - ' + str(pricelist_rec.price)
            res.append((pricelist_rec.id, name))
        return res

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False,
                access_rights_uid=None):
        """Method to get only pricelists of selected product."""
        context = self._context
        if 'kanban_pricelist' in context:
            product_rec = self.env['product.product'].browse(
                [context.get('kanban_pricelist')])
            args += [('product_tmpl_id', '=', product_rec.product_tmpl_id.id)]
        return super(ProductSupplierinfo, self)._search(
            args=args, offset=offset, limit=limit, order=order, count=count,
            access_rights_uid=access_rights_uid)
