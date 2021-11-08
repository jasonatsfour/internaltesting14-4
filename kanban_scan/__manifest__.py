# -*- coding: utf-8 -*-
# © 2018-Today Aktiv Software (http://aktivsoftware.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Kanban",
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
        'kanban_for_manufacturing'],

    'data': [
        'views/menu.xml',
        'views/web_asset_backend_template.xml',
    ],
    'qweb': [
        "static/src/xml/kanban_reordering.xml",
    ],
}
