# -*- coding: utf-8 -*-

from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    octopart = fields.Boolean(string='Octopart')
    octopart_id = fields.Char(string='Octopart Id')
