from odoo import models, fields
from datetime import date


class ShipingInstruction(models.Model):
    _name = 'account.shiping.instruction'
    _description = 'Shiping instruction'

    number_of_packages = fields.Char(string='Number of Pacakges')
    marking = fields.Char(string='Marking')
    net_weight = fields.Float(string='Net Weight')
    gross_weight=fields.Float(string='Gross Weight')
