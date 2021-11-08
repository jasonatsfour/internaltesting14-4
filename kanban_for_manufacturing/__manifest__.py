# -*- coding: utf-8 -*-
# © 2018-Today Aktiv Software (http://aktivsoftware.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Kanban For Manufacturing",
    'summary': """
       """,
    'description': """
    """,
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",
    'category': 'MRP',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'mrp',
        'purchase',
        'stock',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/mrp_kanban_view.xml',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'views/stock_picking_views.xml',
        'views/kanban_reordering.xml',
        'views/menu.xml',
        'report/product_label_report.xml',
        'report/product_label_template.xml',
        'report/report_kfm_barcode.xml',
        'report/report_krr_barcode.xml',
        'report/report_views.xml',
        # 'report/delivery_slip_report.xml',
    ],
}
