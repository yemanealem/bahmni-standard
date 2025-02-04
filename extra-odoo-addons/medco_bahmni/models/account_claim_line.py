from odoo import models, fields
from datetime import date


class AccountClaimLine(models.Model):
    _name = 'account.claim.line'
    _description = 'Claim Line Item'

    claim_id = fields.Many2one('account.claim', string='Claim')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity')
    price_unit = fields.Float(string='Price Unit')
    subtotal = fields.Float(string='Subtotal')
    date = fields.Date(string='Date', default=fields.Date.context_today)
