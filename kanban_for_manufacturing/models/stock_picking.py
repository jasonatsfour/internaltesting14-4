
from odoo import api, models, fields
from odoo.exceptions import ValidationError


class PickingType(models.Model):
    """Class Inherit for adding field."""

    _inherit = "stock.picking.type"

    inter_warehouse = fields.Boolean(
        string='Inter-Warehouse')

    @api.constrains('inter_warehouse')
    def check_inter_warehouse(self):
        """Raise warning if same picking type have more than one record."""
        if self.inter_warehouse:
            stock_picking_type_rec = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.warehouse_id.id),
                    ('code', '=', self.code), ('inter_warehouse', '=', True)])
            if len(stock_picking_type_rec) > 1:
                raise ValidationError(
                    ("""Inter-warehouse of this record is already created.Change the warehouse or change the type of operation."""))


class Picking(models.Model):
    """Class Inherit for adding field."""

    _inherit = "stock.picking"

    picking_status = fields.Char(string='Picking Status')

    @api.model
    def match_barcode(self, barcode):
        """Function call for scan receipt from barcode scanning screen."""
        receipt_rec = self.search([('name', '=', barcode)])
        if receipt_rec:
            receipt_dict = {
                'receipt_record_id': receipt_rec.id,
                'source': receipt_rec.origin,
            }
            receipt_list = []
            receipt_list.append({
                'receipt_id': receipt_rec.id,
                'picking_type_id': receipt_rec.picking_type_id.name,
                'name': receipt_rec.name,
                'source_location': receipt_rec.location_id.display_name,
                'destination_location':
                receipt_rec.picking_type_id.default_location_dest_id.display_name,
                'schedule_date': receipt_rec.scheduled_date,
                'state': receipt_rec.state,
            })
            receipt_dict.update({
                'receipt_list': receipt_list
            })
            return receipt_dict
        else:
            return False

    @api.model
    def confirm_receipt_data(self, receipt_record_id):
        """Function call for validate receipt."""
        receipt_rec = self.browse(receipt_record_id)
        if receipt_rec.state != 'cancel' and receipt_rec.state != 'done':
            for moves in receipt_rec.move_lines:
                moves.update({
                    'quantity_done': moves.product_uom_qty
                })
            receipt_rec.button_validate()
            return {
                'receipt_value': True,
                'stock_receipt': receipt_rec.id,
            }
        else:
            return {
                'receipt_value': False,
            }


class StockMove(models.Model):
    """Class Inherit to add some functionality."""

    _inherit = "stock.move"
    _description = "Stock Move"

    stock_picking_ids = fields.Many2many("stock.picking", string="Receipts")


class StockMoveLine(models.Model):
    """Class Inherit to add some functionality."""

    _inherit = 'stock.move.line'
    _description = "Stock Move Lines"

    # @api.model
    def get_picking(self):
        """Method call for getting receipt number."""
        receipts = [recipt.name for recipt in self.move_id.stock_picking_ids]
        return receipts
