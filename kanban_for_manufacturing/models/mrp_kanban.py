# -*- coding: utf-8 -*-
# © 2018-Today Aktiv Software (http://aktivsoftware.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError


class MrpKanbanReordering(models.Model):
    """Class Call for sacn manufacturing barcode."""

    _name = 'mrp.kanban.reordering'

    name = fields.Char('Name', copy=False)
    product_id = fields.Many2one('product.product', string='Product', domain=[
                                 ('type', 'in', ['product', 'consu']),
                                 ('active', '=', True)])
    product_tmpl_id = fields.Many2one(
        'product.template', related='product_id.product_tmpl_id', store=True)
    reorder_quantity = fields.Integer('Reorder Quantity')
    minimum_quantity = fields.Integer('Minimum Quantity')
    card = fields.Integer('Card')
    card_count = fields.Integer('Card Count')
    barcode = fields.Char('Barcode', copy=False)
    type = fields.Selection([('physical', 'Physical'),
                             ('internal_transfer', 'Internal Transfer'),
                             ('inter_warehouse', 'Inter-Warehouse'),
                             ('manufacturing_order', 'Manufacturing Order')])
    create_delivery_scan = fields.Boolean(
        string="Create Separate Delivery on Scan")
    source_location = fields.Many2one(
        'stock.location', string='Source Location')
    destination_location = fields.Many2one(
        'stock.location', string='Destination Location')
    validate_transfer_on_scan = fields.Boolean('Validate Transfer on Scan')
    auto_release_to_parsable = fields.Boolean('Auto-Release to Parsable')

    @api.model
    def default_get(self, fields):
        """Function call for get default product value."""
        res = super(MrpKanbanReordering, self).default_get(fields)
        if self._context.get('kfm_product_id'):
            product_recs = self.env['product.product'].search(
                [('product_tmpl_id', '=',
                    self._context.get('kfm_product_id'))], limit=1)
            if product_recs:
                res['product_id'] = product_recs.id
        return res

    @api.constrains('source_location', 'destination_location', 'product_id')
    def _check_product_route_ids(self):
        if self.type == 'inter_warehouse':
            if self.source_location and self.destination_location:
                source_warehouse_rec = self.source_location.get_warehouse()
                destination_warehouse_rec = (
                    self.destination_location.get_warehouse())

                if source_warehouse_rec == destination_warehouse_rec:
                    raise ValidationError(
                        _("""Source location and destination location is of same warehouse."""))
                location_route_rec = self.env[
                    'stock.location.route'].search([
                        ('company_id', '=',
                            self.destination_location.company_id.id),
                        ('product_selectable', '=', True)])
                if not location_route_rec:
                    raise ValidationError(
                        _("""Please select the resupply warehouses of the selected source and destination location."""))

                if self.product_id.route_ids.ids:
                    for route in self.product_id.route_ids.ids:
                        if route not in location_route_rec.ids:
                            raise ValidationError(
                                _("""Please select the route_ids in (%s) product of the selected source and destination location""") %
                                self.product_id.name)
                else:
                    raise ValidationError(
                        _("""There is no route_ids was selected in (%s) product""") % self.product_id.name)

    @api.model
    def create(self, vals):
        """Function override for adding sequence."""
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'mrp.kanban.reordering.name') or _('New')
        if vals.get('barcode', _('New')) == _('New'):
            vals['barcode'] = self.env['ir.sequence'].next_by_code(
                'mrp.kanban.reordering.barcode') or _('New')
        return super(MrpKanbanReordering, self).create(vals)

    @api.model
    def match_barcode_generic(self, barcode_krr, barcode_kfm, barcode_receipt):
        """Function call for getting barcode from krr,kfm,receipt."""
        data = {}
        krr_data = self.env['kanban.reordering'].match_barcode(barcode_krr)
        kfm_data = self.match_barcode(barcode_kfm)
        receipt_data = self.env['stock.picking'].match_barcode(barcode_receipt)
        if not krr_data and not kfm_data and not receipt_data:
            return False
        data = {'krr': krr_data, 'kfm': kfm_data, 'receipt': receipt_data}
        return data

    @api.model
    def match_barcode(self, barcode):
        """Function call for match barcode data."""
        reordering_rec = self.search([('barcode', '=', barcode)])
        if reordering_rec:
            kfm_dict = {
                'kfm_id': reordering_rec.id,
                'name': reordering_rec.name,
                'product': reordering_rec.product_id.name,
                'quantity': reordering_rec.reorder_quantity,
                'type': {'internal_transfer': 'Internal Transfer',
                         'inter_warehouse': 'Inter-Warehouse',
                         'manufacturing_order': 'Manufacturing Order',
                         'physical': 'Physical'}[reordering_rec.type],
                'source_location': reordering_rec.source_location.display_name or '-',
                'destination_location':
                    reordering_rec.destination_location.display_name or '-',
                'minimum_quantity': reordering_rec.minimum_quantity
            }
            mrp_list = []
            # Type = Internal Transfer
            if reordering_rec.type == 'internal_transfer':
                stock_picking_id = self.env['stock.picking'].search(
                    [('state', 'not in', ['cancel']),
                        ('origin', '=', reordering_rec.name)],
                    order='id desc', limit=1)
                if stock_picking_id:
                    kfm_dict.update({
                        'current_stock_picking_rec_id': stock_picking_id.id,
                        'current_stock_picking_rec_name': stock_picking_id.name
                    })
                rfq_rec = self.env['stock.picking'].search(
                    [('state', 'not in', ['done', 'cancel']),
                        ('origin', '=', reordering_rec.name)],
                    order='id desc')
                if rfq_rec:
                    rfq_line_recs = rfq_rec.mapped('move_lines').filtered(
                        lambda t: t.product_id.id ==
                        reordering_rec.product_id.id)

                    kfm_dict.update({
                        'internal_transfer_id': rfq_rec[0].id,
                        'schedule_date': datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S")
                    })
                    for rfq_line_rec in rfq_line_recs:
                        mrp_list.append({
                            'internal_transfer_id': rfq_line_rec.picking_id.id,
                            'mrp_number': rfq_line_rec.reference,
                            'source_location':
                            rfq_line_rec.location_id.display_name,
                            'destination_location':
                            rfq_line_rec.location_dest_id.display_name,
                            'qty': rfq_line_rec.product_uom_qty
                        })
                    kfm_dict.update({
                        'mrp_list': mrp_list
                    })
            # Type = Inter Warehouse
            if reordering_rec.type == 'inter_warehouse':
                # Current Delivery Order
                delivery_warehouse_rec = (
                    reordering_rec.source_location.get_warehouse())

                delivery_picking_rec = self.env['stock.picking.type'].search(
                    [('warehouse_id', '=', delivery_warehouse_rec.id),
                        ('code', '=', 'outgoing'),
                        ('inter_warehouse', '=', True)])
                stock_picking_delivery = self.env['stock.picking'].search(
                    [('state', 'not in', ['done', 'cancel']),
                        ('picking_type_id', '=', delivery_picking_rec.id),
                        ('origin', '=', reordering_rec.name)],
                    order='id desc', limit=1)
                kfm_dict.update({
                    'stock_picking_delivery_id': stock_picking_delivery.id,
                    'stock_picking_delivery_name': stock_picking_delivery.name
                })
                # Current Receipt
                receipt_warehouse_rec = (
                    reordering_rec.destination_location.get_warehouse())
                receipt_picking_rec = self.env['stock.picking.type'].search(
                    [('warehouse_id', '=', receipt_warehouse_rec.id),
                        ('code', '=', 'incoming'),
                        ('inter_warehouse', '=', True)])
                stock_picking_receipt = self.env['stock.picking'].search(
                    [('state', 'not in', ['done', 'cancel']),
                        ('picking_type_id', '=', receipt_picking_rec.id),
                        ('origin', '=', reordering_rec.name)],
                    order='id desc', limit=1)
                kfm_dict.update({
                    'stock_picking_receipt_id': stock_picking_receipt.id,
                    'stock_picking_receipt_name': stock_picking_receipt.name
                })

                # List view of Delivery Order
                stock_picking_delivery_details = self.env[
                    'stock.picking'].search(
                    [('state', 'not in', ['cancel']),
                     ('picking_type_id', '=', delivery_picking_rec.id)],
                    order='id desc')
                receipt_state = []
                for picking in stock_picking_delivery_details:
                    for moves in picking.move_lines:
                        receipt_state = [
                            receipt.state for receipt in moves.stock_picking_ids]

                    if picking.state == 'done':
                        if all([x == 'confirmed' for x in receipt_state]):
                            picking.update({'picking_status': 'In Transit'})
                        elif all([x == 'done' for x in receipt_state]):
                            picking.update({'picking_status': 'Done'})
                        elif all([x in ['done', 'confirmed'] for x in receipt_state]):
                            picking.update({'picking_status': 'In Transit'})
                        elif any([x == 'draft' or
                                  x == 'waititng' or
                                  x == 'confirmed' or
                                  x == 'assigned' or
                                  x == 'done' for x in receipt_state]):
                            picking.update(
                                {'picking_status': 'Partially Transit'})
                    else:
                        if picking.state == 'confirmed':
                            picking.update({'picking_status': 'Created'})
                        elif picking.state == 'assigned':
                            picking.update({'picking_status': 'Reserved'})

                final_stock_picking_rec = [
                    picking for picking in stock_picking_delivery_details
                    if picking.origin and
                    reordering_rec.name in picking.origin.split(',')]
                if final_stock_picking_rec:
                    for final_picking in final_stock_picking_rec:
                        if final_picking.picking_status != 'Done':
                            move_line_recs = final_picking[0].mapped(
                                'move_lines').filtered(
                                lambda t: t.product_id.id ==
                                reordering_rec.product_id.id)
                            for move_line_rec in move_line_recs:
                                mrp_list.append({
                                    'delivery_transfer_id':
                                    move_line_rec.picking_id.id,
                                    'delivery_status':
                                    move_line_rec.picking_id.picking_status,
                                    'delivery_scheduled_date':
                                    datetime.datetime.strptime(
                                        str(move_line_rec.picking_id.scheduled_date),
                                        '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y') ,
                                    'mrp_number': move_line_rec.reference,
                                    'source_location':
                                    move_line_rec.location_id.display_name ,
                                    'destination_location':
                                    move_line_rec.location_dest_id.display_name ,
                                    'qty': move_line_rec.product_uom_qty
                                })
                            kfm_dict.update({
                                'mrp_list': mrp_list
                            })
            # Type = Manufacturing Order
            if reordering_rec.type == 'manufacturing_order':
                product_rec = reordering_rec.product_id
                mrp_production_rec = self.env[
                    'mrp.production'].search([
                        ('product_id', '=', product_rec.id),
                        ('state', 'not in', ['done', 'cancel']),
                        ('origin', '=', reordering_rec.name)],
                        order='id desc', limit=1)
                if mrp_production_rec:
                    kfm_dict.update({
                        'current_mrp_production_rec': mrp_production_rec.name,
                        'current_mrp_production_rec_id': mrp_production_rec.id
                    })
                # ['confirmed', 'planned', 'inprogress']
                mrp_production_recs = self.env['mrp.production'].search(
                    [('product_id', '=', product_rec.id),
                        ('state', 'not in', ['done', 'cancel']),
                        ('origin', '=', reordering_rec.name)], order='id desc')
                for production_rec in mrp_production_recs:
                    # production_rec.onchange_product_id()
                    # production_rec._onchange_move_raw()
                    production_rec.update({'product_qty': reordering_rec.reorder_quantity})
                    moves = production_rec.move_raw_ids
                    for move in moves:
                        move.update({'product_uom_qty':production_rec.product_qty * move.product_uom_qty})
                    mrp_list.append({
                        'manuf_id': production_rec.id,
                        'mrp_number': production_rec.name,
                        'source_location':
                        production_rec.location_src_id.display_name or '-',
                        'destination_location':
                        production_rec.location_dest_id.display_name or '-',
                        'qty': production_rec.product_qty
                    })
                kfm_dict.update({
                    'mrp_list': mrp_list
                })
            # Type = Physical
            if reordering_rec.type == 'physical':
                return kfm_dict
            return kfm_dict
        else:
            return False

    @api.model
    def confirm_kfm_data(self, kfm_id):
        """Function call when scan barcode and click on confirm."""
        kfm_rec = self.browse(kfm_id)

        # Type = Physical
        if kfm_rec.type == 'physical':
            return {
                'physical': True}

        # Type = Manufacturing Order
        if kfm_rec.type == 'manufacturing_order':
            bom = self.env['mrp.bom']
            product_rec = kfm_rec.product_id
            product_tmpl_rec = product_rec.product_tmpl_id
            bom_rec = bom.search(
                [('product_tmpl_id', '=', product_tmpl_rec.id)], limit=1)
            if not bom_rec:
                bom_rec = bom.create({
                    'product_tmpl_id': product_tmpl_rec.id,
                    'product_qty': 1,
                    'type': 'normal',
                    'ready_to_produce': 'asap',
                })
                self.env['mrp.bom.line'].create({
                    'product_id': product_rec.id,
                    'product_qty': 1,
                    'bom_id': bom_rec.id
                })

            mrp_production = self.env['mrp.production'].new({
                'product_id': product_rec.id,
                # 'product_qty': kfm_rec.reorder_quantity,
                'bom_id': bom_rec.id,
                'date_planned_start': str(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')),
                'user_id': self.env.user.id,
                'product_uom_id': product_rec.uom_id.id,
                'origin': kfm_rec.name,
                # 'is_child_order': False,
                'company_id': bom_rec.company_id.id,
            })

            mrp_production.onchange_product_id()
            mrp_production._onchange_move_raw()
            mrp = mrp_production._convert_to_write(
                {name: mrp_production[name] for name in mrp_production._cache})
            mrp.update({'product_qty': kfm_rec.reorder_quantity})
            mrp_production_rec = self.env['mrp.production'].create(mrp)
            moves = mrp_production_rec.move_raw_ids
            for move in moves:
                move.update({'product_uom_qty':mrp_production_rec.product_qty * move.product_uom_qty})


            # if auto_release_to_parsable boolean is true
            # for parsable_user if product is created in manufacture_order
            # if mrp_production_rec:
            #     mrp_production_rec.get_onchange_product_parsable_id()
            
            # # if auto_release_to_parsable boolean is true
            # if mrp_production_rec and \
            #         kfm_rec.auto_release_to_parsable:
            #     mrp_production_rec.parsable_job_create()
            return {
                'manufacturing_order': True,
                'manufacturing_order_id': mrp_production_rec.id
            }

        # Type = Internal Transfer
        if kfm_rec.type == 'internal_transfer':
            if self.env['res.config.settings'].search([]):
                con_ids = self.env['res.config.settings'].search(
                    [])[-1].internal_transfer_kanban_id
                # Create picking with waiting stage
                stock_picking_id = self.env['stock.picking'].create({
                    'location_id': kfm_rec.source_location.id,
                    'location_dest_id':kfm_rec.destination_location.id,
                    'origin': kfm_rec.name,
                    'picking_type_id': con_ids.id,
                    'immediate_transfer':True,
                    'move_lines': [(0, 0, {
                         'product_id': kfm_rec.product_id.id,
                         'product_uom_qty':
                         kfm_rec.reorder_quantity,
                         'reserved_availability':
                         kfm_rec.reorder_quantity,
                         'quantity_done': kfm_rec.reorder_quantity,
                         'name': kfm_rec.name,
                         'product_uom':
                         kfm_rec.product_id.uom_id.id})]
                     })
                if stock_picking_id and \
                        kfm_rec.validate_transfer_on_scan:
                    stock_picking_id.button_validate()
            else:
                return {'internal_transfer': False}
            return {
                'internal_transfer': True,
                'internal_picking_id': stock_picking_id.id}

        # Type = Inter Warehouse
        if kfm_rec.type == 'inter_warehouse':
            delivery_warehouse_rec = kfm_rec.source_location.get_warehouse()
            delivery_warehouse = kfm_rec.destination_location.get_warehouse()
            delivery_location = self.env['stock.location'].search(
                [('usage', '=', 'transit'),
                    ('company_id', '=', delivery_warehouse_rec.company_id.id)])
            delivery_picking_rec = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', delivery_warehouse_rec.id),
                    ('code', '=', 'outgoing'), ('inter_warehouse', '=', True)])
            delivery = self.env['stock.picking'].search(
                [('state', 'not in', ['done', 'cancel']),
                 ('picking_type_id', '=', delivery_picking_rec.id),
                 ('partner_id', '=', delivery_warehouse.partner_id.id)],
                order='id desc', limit=1)

            receipt_warehouse_rec = (
                kfm_rec.destination_location.get_warehouse())
            receipt_picking_rec = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', receipt_warehouse_rec.id),
                    ('code', '=', 'incoming'), ('inter_warehouse', '=', True)])
            receipt = self.env['stock.picking'].create({
                'location_id': delivery_location.id,
                'location_dest_id': kfm_rec.destination_location.id,
                'origin': kfm_rec.name,
                'picking_type_id': receipt_picking_rec.id,
                'move_lines': [(0, 0, {
                    'product_id': kfm_rec.product_id.id,
                    'product_uom_qty': kfm_rec.reorder_quantity,
                    'reserved_availability': 0.0,
                    'quantity_done': 0.0,
                    'name': kfm_rec.name,
                    'product_uom': kfm_rec.product_id.uom_id.id})]
            })
            if not kfm_rec.create_delivery_scan and delivery:
                move_line_obj = self.env['stock.move']
                move_line_data = {
                    'picking_id': delivery.id,
                    'product_id': kfm_rec.product_id.id,
                    'stock_picking_ids': [(4, receipt.id)],
                    'product_uom_qty': kfm_rec.reorder_quantity,
                    'reserved_availability': 0.0,
                    'quantity_done': 0.0,
                    'name': kfm_rec.name,
                    'product_uom': kfm_rec.product_id.uom_id.id,
                    'location_id': kfm_rec.source_location.id,
                    'location_dest_id': delivery_location.id
                }
                if not delivery.origin:
                    delivery.update({
                        'origin': kfm_rec.name
                    })
                move_line_obj.create(move_line_data)
                delivery._autoconfirm_picking()
                for moves in delivery.move_lines:
                    if kfm_rec.product_id == moves.product_id:
                        moves.update({
                            'stock_picking_ids': [(4, receipt.id)],
                        })
                exsit_list = []
                if delivery.origin:
                    exsit_list = [True for origin in delivery.origin.split(
                        ',') if origin == kfm_rec.name]
                if not exsit_list:
                    delivery.origin = delivery.origin + ',' + kfm_rec.name
            if kfm_rec.create_delivery_scan or not delivery:
                delivery = self.env['stock.picking'].create({
                    'partner_id': delivery_warehouse.partner_id.id,
                    'location_id': kfm_rec.source_location.id,
                    'location_dest_id': delivery_location.id,
                    'origin': kfm_rec.name,
                    'picking_type_id': delivery_picking_rec.id,
                    'move_lines': [(0, 0, {
                        'product_id': kfm_rec.product_id.id,
                        'stock_picking_ids': [(4, receipt.id)],
                        'product_uom_qty': kfm_rec.reorder_quantity,
                        'reserved_availability': 0.0,
                        'quantity_done': 0.0,
                        'name': kfm_rec.name,
                        'product_uom': kfm_rec.product_id.uom_id.id})]
                })
            delivery.action_confirm()
            receipt.action_confirm()
        return{
            'inter_warehouse': True,
            'delivery_order_id': delivery.id,
            'receipt_id': receipt.id
        }

    @api.model
    def open_picking(self):
        """Function call for open picking from screen."""
        pass
