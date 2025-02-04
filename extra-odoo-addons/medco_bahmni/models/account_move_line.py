from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    eligibility = fields.Char(string="Eligibility")
