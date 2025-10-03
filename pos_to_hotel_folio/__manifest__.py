# -*- coding: utf-8 -*-
{
    'name': 'POS to Hotel Folio',
    'summary': 'Manually push POS order lines to hotel folio lines',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Your Company',
    'website': 'https://example.com',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'hotel_management_odoo'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
    ],
    'assets': {},
    'installable': True,
    'application': False,
}