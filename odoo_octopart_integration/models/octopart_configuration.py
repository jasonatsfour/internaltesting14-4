# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from urllib.request import urlopen
from odoo.tools import ustr
import requests
import json
import itertools
from odoo.addons.odoo_octopart_integration.models.octopart_api import \
    GraphQLClient, get_parts, match_mpns, demo_part_get, demo_match_mpns, demo_get_sellers


class OctopartConfiguration(models.Model):
    _name = 'octopart.configuration'
    _rec_name = 'sequence'
    _order = 'id desc'

    sequence = fields.Char(string='Sequence', default='/')
    api_key = fields.Char(string='Api Key')
    status = fields.Char(string='Status', default='InActive')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('api_key_uniq', 'unique (api_key)', 'Api key must be unique !'),
    ]

    @api.model
    def create(self, values):
        if values.get('sequence', '/') == '/':
            values['sequence'] = self.env['ir.sequence'].next_by_code(
                'octopart.sequence') or '/'
        return super(OctopartConfiguration, self).create(values)

    def get_ready_client(self):
        client = GraphQLClient('https://octopart.com/api/v4/endpoint')
        client.inject_token(self.api_key)
        return client
    #
    def test_connection(self):
        client = self.get_ready_client()
        data = demo_part_get(client)
        # data = demo_get_sellers(client)
        if "errors" not in data:
            self.status = 'Active'
            self._cr.commit()
            raise UserError(_(
                "Connection Test Succeeded! Everything seems properly set up!"
            ))
        else:
            self.status = 'InActive'
            self._cr.commit()
            raise UserError(_(
                "Connection Test Failed! Here is what we got instead:\n %s"
            ) % ustr(','.join([d for d in data])))

    def fetch_octopart_api_details(self, vendor, product, qty, pricelist,
                                   product_code=''):
        client = self.get_ready_client()
        if not vendor or not qty:
            return False

        if not vendor.octopart:
            return False

        uid = ''
        mpns = [product.mpn, pricelist.product_code, product.sku, product_code]

        if vendor.octopart_id:
            uid = vendor.octopart_id

        if not uid:
            return False
        code = pricelist and pricelist.product_code or product_code
        if product.mpn or product.sku or code:
            try:
                octopart_data = match_mpns(
                    client=client, mpns=list(filter(None, mpns)))
                # self._cr.commit()
                price = None
                currency = self.env.user.company_id.currency_id.name
                price_dict = {}
                if "errors" not in octopart_data:
                    for item in octopart_data:
                        all_offers = [list(map(lambda x: x['company']['id'] == uid and x['offers'], i)) for i in list(map(lambda y: y['sellers'], item['parts']))]
                        for offers in all_offers:
                            for offer in list(filter(lambda x: x, offers)):
                                offer = offer[0]
                                company_currency_pricelist = list(
                                    filter(lambda x: x['currency'] == currency, offer['prices'])
                                )
                                company_currency_qty = list(
                                    map(lambda x: x['quantity'] == qty and
                                                  x['quantity'],
                                        company_currency_pricelist)
                                )
                                if any(company_currency_qty):
                                    filtered_list_of_pricelist = list(
                                        filter(lambda x: x['quantity'] == qty,
                                               offer['prices'])
                                    )
                                    if filtered_list_of_pricelist:
                                        price = filtered_list_of_pricelist[0][
                                            'price']
                                        price_dict.update({
                                            'price': float(price),
                                            })
                                    else:
                                        price_dict.update({
                                            'price': company_currency_pricelist[0][
                                                'price'],
                                        })
                    # if not price_dict.get('price', False):
                        # raise UserError(_(
                        #     "Sorry! Price not fetched from "
                        #     "octopart as price is not "
                        #     "available in company's currency"))
                    return price_dict
            except Exception as e:
                raise UserError(_(e))

    def is_less_than(self, list, num):
        result_list = [i for i in list if i and i <= num]
        return result_list and max(result_list)
