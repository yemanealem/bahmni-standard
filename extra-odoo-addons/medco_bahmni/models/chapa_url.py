import uuid
import requests
from odoo import models, fields

class ChapUrl(models.Model):
    _name = 'chap.url'
    _description = 'Chapa Payment URL Management'

    tx_ref = fields.Char(string="Transaction Reference", required=True)
    callback_url = fields.Char(string="Chapa Url", required=True)
    payment_status = fields.Selection([('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
                                      default='pending', string="Payment Status")
    
    