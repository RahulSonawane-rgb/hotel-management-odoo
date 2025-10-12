{
    'name': 'POS to Hotel Folio',
    'summary': 'Integrate Point of Sale with Hotel Folios for seamless billing.',
    'description': """
POS to Hotel Folio Connector
============================
This module provides a powerful integration between Odoo's Point of Sale and Hotel Management applications.

Key Features:
-------------
*   **Send to Folio:** Replaces the standard payment button in POS with a "Send to Folio" button for restaurant orders.
*   **Room Selection:** Allows cashiers to select an occupied room with an active folio.
*   **Automatic Folio Update:** Automatically adds the POS order items as service lines to the guest's hotel folio.
*   **Backend Integration:** View the linked room from the POS order and see POS charges directly on the folio.
    """,
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Rahul Sonawane',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'pos_restaurant', 'hotel_management_odoo'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        'views/room_booking_views.xml',
        'views/room_booking_beneficiary_view.xml',
        'views/account_move_report.xml'
    ],
    'images': [
        'static/description/icon.png',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_to_hotel_folio/static/src/js/pos_hotel_folio.js',
            'pos_to_hotel_folio/static/src/xml/pos_hotel_folio.xml',
        ],
    },
    'installable': True,
    'application': True,
}
