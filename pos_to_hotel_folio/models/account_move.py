from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    booking_id = fields.Many2one('room.booking', string='Hotel Booking', help='Related hotel booking (folio).')
    beneficiary_id = fields.Many2one('res.partner', string='Beneficiary', help='Beneficiary carried from the booking, if any.')

