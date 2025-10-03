# -*- coding: utf-8 -*-
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

    available_room_ids = fields.Many2many(
        'hotel.room',
        string='Available Rooms (Active Folios)',
        compute='_compute_available_room_ids',
        help='Helper field used to restrict selectable rooms to those with an active folio.'
    )

    @api.depends()
    def _compute_available_room_ids(self):
        # Rooms that have at least one booking in draft or check_in state
        BookingLine = self.env['room.booking.line']
        active_lines = BookingLine.search([
            ('booking_id.state', 'in', ['draft', 'check_in'])
        ])
        room_ids = active_lines.mapped('room_id').ids
        for order in self:
            order.available_room_ids = [(6, 0, room_ids)]

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

            # Create service lines in folio based on POS order lines
            for line in order.lines:
                product = line.product_id
                quantity = line.qty
                price_unit = line.price_unit

                # Map each POS line to a hotel.service to preserve pricing
                hotel_service = self.env['hotel.service'].search([('name', '=', product.display_name)], limit=1)
                if not hotel_service:
                    hotel_service = self.env['hotel.service'].create({
                        'name': product.display_name,
                        'unit_price': price_unit,
                    })
                self.env['service.booking.line'].create({
                    'booking_id': booking.id,
                    'service_id': hotel_service.id,
                    'uom_qty': quantity,
                })

            order.sent_to_folio = True
        return True
