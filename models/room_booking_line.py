# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADARSH K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class RoomBookingLine(models.Model):
    """Model that handles the room booking form"""
    _name = "room.booking.line"
    _description = "Hotel Folio Line"
    _rec_name = 'room_id'

    @tools.ormcache()
    def _set_default_uom_id(self):
        return self.env.ref('uom.product_uom_day')

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 help="Indicates the Room",
                                 ondelete="cascade")
    checkin_date = fields.Datetime(string="Check In",
                                   help="You can choose the date,"
                                        " Otherwise sets to current Date",
                                   required=True)
    checkout_date = fields.Datetime(string="Check Out",
                                    help="You can choose the date,"
                                         " Otherwise sets to current Date",
                                    required=True)
    room_id = fields.Many2one('hotel.room', string="Room",
                              help="Indicates the Room",
                              required=True)
    uom_qty = fields.Float(string="Duration",
                           help="The quantity converted into the UoM used by "
                                "the product", readonly=True)
    uom_id = fields.Many2one('uom.uom',
                             default=_set_default_uom_id,
                             string="Unit of Measure",
                             help="This will set the unit of measure used",
                             readonly=True)
    price_unit = fields.Float(related='room_id.list_price', string='Rent',
                              digits='Product Price',
                              help="The rent price of the selected room.")
    tax_ids = fields.Many2many('account.tax',
                               'hotel_room_order_line_taxes_rel',
                               'room_id', 'tax_id',
                               related='room_id.taxes_ids',
                               string='Taxes',
                               help="Default taxes used when selling the room."
                               , domain=[('type_tax_use', '=', 'sale')])
    currency_id = fields.Many2one(string='Currency',
                                  related='booking_id.pricelist_id.currency_id'
                                  , help='The currency used')
    price_subtotal = fields.Float(string="Subtotal",
                                  compute='_compute_price_subtotal',
                                  help="Total Price excluding Tax",
                                  store=True)
    price_tax = fields.Float(string="Total Tax",
                             compute='_compute_price_subtotal',
                             help="Tax Amount",
                             store=True)
    price_total = fields.Float(string="Total",
                               compute='_compute_price_subtotal',
                               help="Total Price including Tax",
                               store=True)
    state = fields.Selection(related='booking_id.state',
                             string="Order Status",
                             help=" Status of the Order",
                             copy=False)
    booking_line_visible = fields.Boolean(default=False,
                                          string="Booking Line Visible",
                                          help="If True, then Booking Line "
                                               "will be visible")

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_date(self):
        """When you change checkin_date or checkout_date it will check
        and update the qty of hotel service line
        -----------------------------------------------------------------
        @param self: object pointer"""
        if self.checkout_date < self.checkin_date:
            raise ValidationError(
                _("Checkout must be greater or equal checkin date"))
        if self.checkin_date and self.checkout_date:
            diffdate = self.checkout_date - self.checkin_date
            qty = diffdate.days
            if diffdate.total_seconds() > 0:
                qty = qty + 1
            self.uom_qty = qty

    @api.depends('uom_qty', 'price_unit', 'tax_ids','currency_id')
    def _compute_price_subtotal(self):
        """Compute the amounts of the room booking line."""
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env['account.tax']._add_tax_details_in_base_line(base_line, self.env.company)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal
            if self.env.context.get('import_file',
                                    False) and not self.env.user. \
                    user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_recordset(
                    ['invoice_repartition_line_ids'])

    def _prepare_base_line_for_taxes_computation(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """

        self.ensure_one()
        if not self.booking_id.pricelist_id:
            self.currency_id = self.env.company.currency_id
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **{
                'tax_ids': self.tax_ids,
                'quantity': self.uom_qty,
                'partner_id': self.booking_id.partner_id,
                'currency_id': self.currency_id,
            },
        )

    @api.onchange('checkin_date', 'checkout_date', 'room_id')
    def onchange_checkin_date(self):
        """On change of check-in date, check-out date, or room ID,
           this method validates if the selected room is available
           for the given dates. It searches for existing bookings
           in the 'reserved' or 'check_in' state and checks for date
           conflicts. If a conflict is found, a ValidationError is raised."""
        records = self.env['room.booking'].search(
            [('state', 'in', ['reserved', 'check_in'])])
        for rec in records:
            rec_room_id = rec.room_line_ids.room_id
            rec_checkin_date = rec.room_line_ids.checkin_date
            rec_checkout_date = rec.room_line_ids.checkout_date
            if rec_room_id and rec_checkin_date and rec_checkout_date:
                # Check for conflicts with existing room lines
                for line in self:
                    if line.id != rec.id and line.room_id == rec_room_id:
                        # Check if the dates overlap
                        if (rec_checkin_date <= line.checkin_date <= rec_checkout_date or
                                rec_checkin_date <= line.checkout_date <= rec_checkout_date):
                            raise ValidationError(
                                _("Sorry, You cannot create a reservation for "
                                  "this date since it overlaps with another "
                                  "reservation..!!"))
                        if rec_checkout_date <= line.checkout_date and rec_checkin_date >= line.checkin_date:
                            raise ValidationError(
                                "Sorry You cannot create a reservation for this"
                                "date due to an existing reservation between "
                                "this date")
                            
    def _get_target_status_from_booking_state(self):
        """Return the desired room status and availability based on the
        parent booking's state.

        - reserved -> ("reserved", False)
        - check_in -> ("occupied", False)
        - otherwise -> (None, None)
        """
        self.ensure_one()
        state = self.booking_id.state
        if state == 'reserved':
            return 'reserved', False
        if state == 'check_in':
            return 'occupied', False
        return None, None

    def _recompute_room_status(self, room):
        """Recompute and set the status for the given room considering all
        active bookings (reserved/check_in) that reference it.

        Priority: check_in -> occupied; reserved -> reserved; none -> available
        """
        if not room:
            return
        lines = self.env['room.booking.line'].search([
            ('room_id', '=', room.id),
            ('booking_id.state', 'in', ['reserved', 'check_in']),
        ])
        if lines.filtered(lambda l: l.booking_id.state == 'check_in'):
            room.write({'status': 'occupied', 'is_room_avail': False})
        elif lines:
            room.write({'status': 'reserved', 'is_room_avail': False})
        else:
            room.write({'status': 'available', 'is_room_avail': True})

    @api.model
    def create(self, vals):
        """Synchronize room status when adding a line to an already
        reserved or checked-in booking."""
        record = super().create(vals)
        status, is_room_avail = record._get_target_status_from_booking_state()
        if status and record.room_id:
            record.room_id.write({'status': status, 'is_room_avail': is_room_avail})
        return record

    def write(self, vals):
        """When room changes, free the previous room and set the new room's
        status based on the parent booking's state."""
        old_rooms_by_line_id = {}
        if 'room_id' in vals:
            for line in self:
                old_rooms_by_line_id[line.id] = line.room_id
        result = super().write(vals)
        if 'room_id' in vals:
            for line in self:
                old_room = old_rooms_by_line_id.get(line.id)
                new_room = line.room_id
                if old_room and new_room and old_room != new_room:
                    # Recompute status for old room considering other bookings
                    line._recompute_room_status(old_room)
                    # Set status for new room according to this booking's state
                    status, is_room_avail = line._get_target_status_from_booking_state()
                    if status:
                        new_room.write({'status': status, 'is_room_avail': is_room_avail})
        return result

    def unlink(self):
        """When removing the line, release the room if no other active
        bookings hold it."""
        rooms = self.mapped('room_id')
        result = super().unlink()
        for room in rooms:
            self._recompute_room_status(room)
        return result
