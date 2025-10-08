from odoo import fields, models


class RoomBooking(models.Model):
    _inherit = 'room.booking'

    beneficiary_id = fields.Many2one(
        'res.partner',
        string='Beneficiary',
        help='Deprecated: use Beneficiaries below.',
        domain="[('parent_id','=',partner_id)]",
    )
    beneficiary_ids = fields.Many2many(
        'res.partner',
        'room_booking_beneficiary_rel',
        'booking_id',
        'partner_id',
        string='Beneficiaries',
        help='Optional beneficiaries/guests under the main customer.',
        domain="[('parent_id','=',partner_id)]",
    )

    def action_invoice(self):
        res = super().action_invoice()
        # Link created invoice to booking and set beneficiary if available
        if isinstance(res, dict) and res.get('res_id'):
            invoice = self.env['account.move'].browse(res['res_id'])
            for booking in self:
                invoice.write({
                    'booking_id': booking.id,
                    'beneficiary_id': booking.beneficiary_id.id or False,
                    'beneficiary_ids': [(6, 0, booking.beneficiary_ids.ids)],
                })
        return res

