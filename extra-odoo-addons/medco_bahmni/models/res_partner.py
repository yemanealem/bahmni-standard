from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    cbhiId = fields.Char(string="CBHI ID", help="Community-Based Health Insurance ID")
    
