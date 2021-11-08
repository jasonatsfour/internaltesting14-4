# -*- coding: utf-8 -*-
# Update
{
    'name': 'Octopart Integration',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Misc',
    'summary': 'Octopart Integration',
    'description': 'Octopart Integration',
    'author': "",
    'website': "",
    'depends': [
        'base', 'purchase', 'web', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/webclients_templates.xml',
        'views/octopart_configuration_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'views/res_partner_view.xml',
        'views/purchase_views.xml',
        'views/octopart_seller_details_view.xml',
        'wizard/update_octopart_price.xml',
        'wizard/view_fetch_seller_details.xml',
        'wizard/view_vendor_pricelist_create.xml',
        'wizard/view_add_octopart_wizard.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
