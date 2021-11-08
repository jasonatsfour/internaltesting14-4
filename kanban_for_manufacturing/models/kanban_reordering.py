# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class KanbanReordering(models.Model):
    """Class for kanban Re-Ordering Rules."""

    _name = 'kanban.reordering'

    name = fields.Char(string="Name", required=1,
                       default=lambda self: _('New'),copy=False)
    product_id = fields.Many2one(
        "product.product", string="Product", required=1)
    product_tmpl_id = fields.Many2one(
        'product.template', related='product_id.product_tmpl_id', store=True)
    pricelist_id = fields.Many2one("product.supplierinfo",
                                   string="Pricelist",
                                   required=1)
    reorder_qty = fields.Char(string="Reorder Quantity")
    minimun_qty = fields.Char(string="Minimum Quantity")
    automatic_confirm = fields.Boolean(
        string="Confirm RFQ automatically?")
    barcode = fields.Char(string="Barcode", copy=False,
                          default=lambda self: _('New'))
    target_location_id = fields.Many2one(
        "stock.location", string="Target Location")
    card = fields.Integer(string="Card")
    card_count = fields.Integer(string="Card Count")

    _sql_constraints = [
        ('barcode_uniq', 'unique(barcode)',
         "A barcode can only be assigned to one Kanban Reordering rule !"),
    ]

    @api.model
    def default_get(self, fields):
        """Function call for get default product value."""
        res = super(KanbanReordering, self).default_get(fields)
        if self._context.get('krr_product_id'):
            product_recs = self.env['product.product'].search(
                [('product_tmpl_id', '=',
                    self._context.get('krr_product_id'))], limit=1)
            if product_recs:
                res['product_id'] = product_recs.id
        return res

    @api.model
    def create(self, vals):
        """Create Method Override for add sequence."""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'kanban.reordering.name') or _('New')
        if vals.get('barcode', _('New')) == _('New'):
            vals['barcode'] = self.env['ir.sequence'].next_by_code(
                'kanban.reordering.barcode') or _('New')
        return super(KanbanReordering, self).create(vals)

    @api.model
    def match_barcode(self, barcode):
        """Function Call for Metch Barcode which scab by user."""
        reordering_rec = self.search([('barcode', '=', barcode)])
        if reordering_rec:
            kkr_dict = {
                'kkr_id': reordering_rec.id,
                'name': reordering_rec.name,
                'product': reordering_rec.product_id.name,
                'vendor': reordering_rec.pricelist_id.name.name,
                'quantity': reordering_rec.reorder_qty or 0
            }
            # Purhchase Order
            purchase_list = []
            # RFQ
            rfq_rec = self.env['purchase.order'].search([
                ('partner_id', '=', reordering_rec.pricelist_id.name.id),
                ('state', 'in', ['draft', 'sent'])],
                order='id desc')
            if rfq_rec:
                rfq_line_recs = rfq_rec.mapped('order_line').filtered(
                    lambda t: t.product_id.id == reordering_rec.product_id.id)
                kkr_dict.update({
                    'purchase_id': rfq_rec[0].id,
                    'purchase_exist': True,
                    'current_purchase_order_rec_name': rfq_rec[0].name,
                })
                for rfq_line_rec in rfq_line_recs:
                    purchase_list.append({
                        'purchase_type': 'RFQ',
                        'purchase_number': rfq_line_rec.order_id.name,
                        'purchase_id': rfq_line_rec.order_id.id,
                        'purchase_vendor':
                        rfq_line_rec.order_id.partner_id.name,
                        'purchase_qty': rfq_line_rec.product_qty,
                        'received_qty': rfq_line_rec.qty_received,
                        'purchase_scheduled_date': rfq_line_rec.date_planned
                    })
            # Purchase Order
            purchase_recs = self.env['purchase.order'].search([
                ('partner_id', '=', reordering_rec.pricelist_id.name.id),
                ('state', 'not in', ['draft', 'sent', 'done', 'cancel']),
                ('order_line.product_id', '=', reordering_rec.product_id.id)])
            if purchase_recs:
                po_line_recs = purchase_recs.mapped('order_line').filtered(
                    lambda t: t.product_id.id ==
                    reordering_rec.product_id.id and
                    t.product_qty != t.qty_received)
                for po_line_rec in po_line_recs:
                    purchase_list.append({
                        'purchase_type': 'PO',
                        'purchase_number': po_line_rec.order_id.name,
                        'purchase_vendor':
                        po_line_rec.order_id.partner_id.name,
                        'purchase_id': po_line_rec.order_id.id,
                        'purchase_qty': po_line_rec.product_qty,
                        'received_qty': po_line_rec.qty_received,
                        'purchase_scheduled_date': po_line_rec.date_planned
                    })
            kkr_dict.update({
                'purchase_list': purchase_list
            })
            return kkr_dict
        else:
            return False

    @api.model
    def create_po(self, kkr_id):
        """Function call for createPurchase Oder."""
        kkr_rec = self.browse(kkr_id)
        # PO
        po_obj = self.env['purchase.order']
        po_id = po_obj.new({'partner_id': kkr_rec.pricelist_id.name.id})
        po_id.onchange_partner_id()
        po_dict = po_obj._convert_to_write(
            {name: po_id[name] for name in po_id._cache})
        po_dict.update({'company_id': self.env.user.company_id.id})
        po_order_rec = po_obj.create(po_dict)
        purchase_id = po_order_rec.id
        purchase_name = po_order_rec.name
        # PO line
        pol_obj = self.env['purchase.order.line']
        po_line_id = pol_obj.new({'product_id': kkr_rec.product_id.id,
                                  'order_id': po_order_rec.id,
                                  'partner_id': po_order_rec.partner_id.id})
        po_line_id.onchange_product_id()
        po_line_dict = pol_obj._convert_to_write(
            {name: po_line_id[name] for name in po_line_id._cache})
        po_line_dict.update({'price_unit': kkr_rec.pricelist_id.price,
                             'product_qty': kkr_rec.reorder_qty})
        po_line_rec = pol_obj.create(po_line_dict)
        # Here we are calling method from digikey module to fetch the price of
        # digikey vendor
        # po_line_rec.get_details()
        if kkr_rec.automatic_confirm:
            po_order_rec.button_approve()
        return [purchase_id, purchase_name]

    @api.model
    def update_po(self, purchase_id, kkr_id):
        """Function call for Update Purchase Order."""
        kkr_rec = self.browse(kkr_id)
        purchase_rec = self.env['purchase.order'].browse(purchase_id)
        # PO line
        pol_obj = self.env['purchase.order.line']
        po_line_id = pol_obj.new({'product_id': kkr_rec.product_id.id,
                                  'order_id': purchase_rec.id,
                                  'partner_id': purchase_rec.partner_id.id})
        po_line_id.onchange_product_id()
        po_line_dict = pol_obj._convert_to_write(
            {name: po_line_id[name] for name in po_line_id._cache})
        po_line_dict.update({'price_unit': kkr_rec.pricelist_id.price,
                             'product_qty': kkr_rec.reorder_qty})
        po_line_rec = pol_obj.create(po_line_dict)
        # Here we are calling method from digikey module to fetch the price of
        # digikey vendor
        # po_line_rec.get_details()
        return True

