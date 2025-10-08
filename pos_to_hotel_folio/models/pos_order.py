from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    room_id = fields.Many2one(
        'hotel.room',
        string='Room',
        help='Link the POS order to a hotel room with an active folio.',
    )
    sent_to_folio = fields.Boolean(
        string='Sent to Folio',
        default=False,
        readonly=True,
        help='Indicates whether this order was already transferred to a hotel folio.'
    )

    occupied_room_ids = fields.Many2many(
        'hotel.room',
        string='Occupied Rooms (Active Folios)',
        compute='_compute_occupied_room_ids',
        help='Rooms with active folios (status != Available).'
    )

    @api.depends()
    def _compute_occupied_room_ids(self):
        BookingLine = self.env['room.booking.line']
        active_lines = BookingLine.search([
            ('booking_id.state', 'in', ['draft', 'check_in'])
        ])
        room_ids = active_lines.mapped('room_id').ids
        for order in self:
            order.occupied_room_ids = [(6, 0, room_ids)]

    @api.model
    def get_occupied_rooms(self):
        BookingLine = self.env['room.booking.line']
        active_lines = BookingLine.search([
            ('booking_id.state', 'in', ['draft', 'check_in'])
        ])
        rooms = active_lines.mapped('room_id')
        return [{'id': room.id, 'name': room.display_name} for room in rooms] if rooms else []

    def _get_active_booking_for_room(self, room):
        self.ensure_one()
        Booking = self.env['room.booking']
        return Booking.search([
            ('state', 'in', ['draft', 'check_in']),
            ('room_line_ids.room_id', '=', room.id),
        ], limit=1, order='id desc')

    def action_send_to_folio(self):
        for order in self:
            if order.sent_to_folio:
                raise UserError(_('This order was already sent to folio.'))
            if not order.room_id:
                raise UserError(_('Please select a room before sending to folio.'))

            booking = order._get_active_booking_for_room(order.room_id)
            if not booking:
                raise UserError(_('No active folio found for the selected room.'))

            # Create service lines in folio (no category; appears in services section via module UI)
            for line in order.lines:
                product = line.product_id
                quantity = line.qty
                price_unit = line.price_unit

                hotel_service = self.env['hotel.service'].search([
                    ('name', '=', product.display_name),
                ], limit=1)
                if not hotel_service:
                    hotel_service = self.env['hotel.service'].create({
                        'name': product.display_name,
                        'unit_price': price_unit,
                        # No category_id; Cybrosys module uses default service type or UI grouping for "Food"
                    })
                self.env['service.booking.line'].create({
                    'booking_id': booking.id,
                    'service_id': hotel_service.id,
                    'uom_qty': quantity,
                    'pos_order_date': order.date_order,
                    'pos_table_id': getattr(order, 'table_id', False) and order.table_id.id or False,
                })

            order.sent_to_folio = True
            order.state = 'done'
        return True