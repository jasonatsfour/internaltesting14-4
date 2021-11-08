# -*- coding: utf-8 -*-
from odoo import api, models, _
from urllib.request import urlopen
# from urllib2 import urlopen
import json
import logging
from odoo.addons.odoo_octopart_integration.models.octopart_api import \
    match_mpns


_logger = logging.getLogger(__name__)


class FetchSeller(models.TransientModel):
    """
    This wizard will fetch seller's octopart details from Octopart
    """
    _name = 'fetch.sellers'
    _description = 'Fetch Seller Details'

    
    def fetch_seller_details(self):
        res = self.env['fetch.seller.detail'].search(
            [], limit=1).fetch_seller_details()
        return res


class FetchSellerDetail(models.TransientModel):
    """
    This wizard will fetch seller's octopart details from Octopart
    """
    _name = 'fetch.seller.detail'
    _description = 'Fetch Seller Details'

    def fetch_seller_details(self):
        seller_obj = self.env['octopart.seller.detail']
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        sellers_dict = []
        api_key = None
        octopart_config = self.env['octopart.configuration'].search([(
            'status', '=', 'Active')], limit=1, order='id desc')
        if octopart_config:
            api_key = octopart_config.api_key
        client = octopart_config.get_ready_client()
        self.env['octopart.seller.detail'].search([]).sudo().unlink()
        for product in self.env['product.template'].browse(active_ids):
            if api_key and product.sku or product.mpn:
                mpns = [product.mpn, product.sku]
                fetched_list = self.fetch_detail(client, mpns) or []
                sellers_dict = sellers_dict + fetched_list

        sellers_ids = []
        for values in sellers_dict:
            sellers_ids.append(seller_obj.sudo().create(values).id)
        self._cr.commit()
        view_id = self.env.ref(
            'odoo_octopart_integration.octopart_seller_detail_tree_view')
        tree_view = {
            'name': _('Octopart Seller Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'octopart.seller.detail',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id.id, 'tree')],
            'domain': [('id', 'in', sellers_ids)],
        }
        return tree_view

    def fetch_detail(self, client, query):
        try:
            sellers_dict = []
            self.env['octopart.seller.detail'].search([]).unlink()
            octopart_data = match_mpns(client=client, mpns=list(filter(False or None, query)))
            currency = self.env.user.company_id.currency_id
            if octopart_data:
                # This for loop for the multiple records
                for result in octopart_data:
                    # This for loop for the multiple parts
                    for item in result['parts']:
                        # This for loop for the multiple sellers in parts
                        for seller in item['sellers']:
                            uid = seller['company']['id']
                            # This for loop for the multiple seller's
                            # multiple offers
                            for offer in seller['offers']:
                                company_currency_pricelist = list(
                                    filter(lambda x: x['currency'] == currency.name,
                                           offer['prices'])
                                )
                                for pricelist in company_currency_pricelist:
                                    sku_product = self.env[
                                        'product.template'].search(
                                        [('mpn', '=', item['mpn'])],
                                        limit=1)
                                    description_dict = list(filter(
                                        lambda d: d['credit_string'] == item['manufacturer']['name'], item['descriptions'])
                                    )
                                    existing_sellers_dict = list(filter(
                                        lambda x: x['product_tmpl_id'] == sku_product.id and x['name'] == seller['company']['name'] and x['sku'] == offer['sku'], sellers_dict
                                    ))
                                    if existing_sellers_dict:
                                        vals = existing_sellers_dict[0]
                                    else:
                                        vals = {
                                            'product_tmpl_id': sku_product and sku_product.id,
                                            'name': seller['company']['name'],
                                            'min_qty': offer['moq'],
                                            'uid': uid,
                                            'description': description_dict and description_dict[0]['text'] or '',
                                            'sku': offer['sku'],
                                            'stock': offer['inventory_level'],
                                            'pkg': offer['packaging'],
                                            'last_updated': offer['updated'].replace('T', ' ').replace('Z', ''),
                                            'currency_id': currency.id,
                                            # Cache id of price built like this country-currency-ppid_of_offer-company_id-pricelist_id-quantity-price(in default currency)
                                            # So we will get pricelist id
                                            'octopart_pricelist_id': pricelist['_cache_id'].split('-')[4],
                                        }
                                    if pricelist['quantity'] == 1:
                                        vals.update({
                                            'qty_1': pricelist['price'],
                                        })
                                    if pricelist['quantity'] == 10:
                                        vals.update({
                                            'qty_10': pricelist['price'],
                                        })
                                    if pricelist['quantity'] == 100:
                                        vals.update({
                                            'qty_100': pricelist['price'],
                                        })
                                    if pricelist['quantity'] == 1000:
                                        vals.update({
                                            'qty_1000': pricelist['price'],
                                        })
                                    if pricelist['quantity'] == 10000:
                                        vals.update({
                                            'qty_10000': pricelist['price'],
                                        })
                                    if vals not in sellers_dict:
                                        sellers_dict.append(vals)
            return sellers_dict
        except Exception as e:
            raise e
