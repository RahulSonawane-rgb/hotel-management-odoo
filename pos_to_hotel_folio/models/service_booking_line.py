from odoo import fields, models


class ServiceBookingLine(models.Model):
    _inherit = 'service.booking.line'

    pos_order_date = fields.Datetime(string='Date', help='Order date coming from POS when sent to folio.')
    pos_table_id = fields.Many2one('restaurant.table', string='Table', help='Restaurant table used in POS for this order.')

