from odoo import http
from odoo.http import request


class GetPurchaseOrder(http.Controller):

    @http.route(
        '/open/purchase/<model("purchase.order"):purchase_id>',
        type='http', auth='public')
    def open_purchase_order(self, purchase_id, **kw):
        form_view = request.env.ref('purchase.purchase_order_form').id
        tree_view = request.env.ref('purchase.purchase_order_tree').id
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')

        record_url = base_url + "/web#id=" + \
            str(purchase_id.id) + "&view_type=form&model='purchase.order'"
        client_action = {
            'type': 'ir.actions.act_url',
            'name': "Purchase Order",
            'target': 'new',
            'url': record_url,
        }

        return client_action
        # return {
        #     'name': "Purchase Order",
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'tree',
        #     'view_mode': 'form',
        #     'views': [(tree_view, 'list'), (form_view, 'form')],
        #     'res_id': purchase_id.id,
        #     'res_model': 'purchase.order',
        #     'view_id': form_view,
        #     'target': 'new',
        # }
