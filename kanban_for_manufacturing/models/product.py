# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ProductProduct(models.Model):
    """Class Inherit for add Some functions."""

    _inherit = "product.product"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Method is used to get product of the selected type in kanbancard."""
        domain = []
        if args is None:
            args = []
        if self._context.get('type') == 'manufacturing_order':
            domain = [('bom_ids', '!=', False),
                      ('bom_ids.active', '=', True),
                      ('bom_ids.type', '=', 'normal')]
        return super(
            ProductProduct, self).name_search(
            name, args=args + domain, operator=operator, limit=limit)


class ProductTemplate(models.Model):
    """Class Inherit for store kanban details in product."""

    _inherit = "product.template"

    kfm_ids = fields.One2many(
        'mrp.kanban.reordering', 'product_tmpl_id',
        string="Kanban From Manufacturing")
    krr_ids = fields.One2many(
        'kanban.reordering', 'product_tmpl_id',
        string="Kanban Re-Ordering")
