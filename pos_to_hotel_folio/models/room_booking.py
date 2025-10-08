from odoo import fields, models


class RoomBooking(models.Model):
    _inherit = 'room.booking'

    beneficiary_id = fields.Many2one(
        'res.partner',
        string='Beneficiary',
        help='Optional beneficiary/guest under the main customer (e.g., employee of a company).',
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
                })
        return res

