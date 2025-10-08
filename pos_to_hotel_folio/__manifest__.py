{
    'name': 'POS to Hotel Folio',
    'summary': 'Manually push POS order lines to hotel folio lines',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Your Company',
    'website': 'https://example.com',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'pos_restaurant', 'hotel_management_odoo'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        'views/room_booking_views.xml',
        'views/room_booking_beneficiary_view.xml',
        'views/account_move_report.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_to_hotel_folio/static/src/js/pos_hotel_folio.js',
            'pos_to_hotel_folio/static/src/xml/pos_hotel_folio.xml',
        ],
    },
    'installable': True,
    'application': False,
}