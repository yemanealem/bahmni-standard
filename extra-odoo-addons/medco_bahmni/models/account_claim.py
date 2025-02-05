from odoo import models, fields,api
import random
import logging
import requests
import uuid
import time
import json
from datetime import date
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountClaim(models.Model):
    _name = 'account.claim' 
    _description = 'Claim Management'

    hospital_name = fields.Text(string='Hospital Name')
    amount = fields.Float(string='Amount')
    date = fields.Date(string='Claim Date', default=fields.Date.today)
    cbhi_id = fields.Text(string='Cbhi ID')
    claim_number = fields.Char(string='Claim Number', readonly=True)


    state = fields.Selection([
        ('draft', 'draft'),
        ('Requested','Requested'),
        ('Processed', 'Processed'),
        ('Approved', 'Approved'),
        ('Checked','Checked'),
        ('Rejected', 'Rejected'),
        ('Authorized','Authorized'),
        ('Settled','Settled'),
        ('Rejected','Rejected'),
        ('paid', 'paid'),
    ], string='State', default='draft')

    
    partner_id = fields.Many2one('res.partner', string='Patient')  
    
    invoice_id = fields.Many2one('account.move', string='Invoice')
    
    claim_line_ids = fields.One2many('account.claim.line', 'claim_id', string='Products')


    @api.model
    def create(self, vals):
        record = super(AccountClaim, self).create(vals)
        current_year = date.today().year
        sequence = self.env['ir.sequence'].next_by_code('claim.number.sequence')
        if sequence.startswith('CLM/'):
            sequence_number = sequence.replace('CLM/', '', 1)
            record.claim_number = 'CLM/ZEWDITU/{}/{}'.format(current_year, sequence_number)

        
        return record


    def action_send_claims(self):

        claims_data = self.read([
            'partner_id', 'hospital_name', 'invoice_id', 'amount','claim_number', 'date', 'cbhi_id', 'state', 'claim_line_ids'
        ])

        formatted_data = []

        for claim in claims_data:
            claim_dict = {
                "cbhiId": claim['cbhi_id'], 
                "providerName": "Zewditu",
                "claimId":claim['claim_number'],
                "description":"",
                "services": []
            }

            if claim.get("claim_line_ids"):
                claim_lines = self.env["account.claim.line"].browse(claim["claim_line_ids"])
                claim_dict["services"] = [
                    {"serviceName": line.product_id.name, "serviceDate": str(claim["date"]),"servicePrice":str(line.subtotal)}
                    for line in claim_lines
                ]

            formatted_data.append(claim_dict)
            _logger.info("Sending data to API:\n%s", json.dumps(formatted_data, indent=4))


        url = "http://192.168.210.196:8900/api/cbhi/claim"
        headers = {'Content-Type': 'application/json'}

        try:
            _logger.info("Claim data data: %s", formatted_data)

            response = requests.post(url, json=formatted_data, timeout=100)


            if response.status_code == 200:
                for claim in claims_data:
                    claim_record = self.env['account.claim'].browse(claim['id'])
                    
                    if claim_record.exists():
                        claim_record.write({'state': 'processing'})

                message = "✅ CLaim Sent Successfully for Proceess"
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {'message': message})
                 
            else:
                _logger.error("Error sending claims: %s - %s", response.status_code, response.text)
                raise UserError(f"Error sending claims: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            _logger.error("Request timed out while sending claims.")
            raise UserError("Request timed out. Please try again later.")
        
        except requests.exceptions.ConnectionError:
            _logger.error("Failed to connect to the external claim system.")
            raise UserError("Failed to connect to the external system. Check network connectivity.")
        
        except requests.exceptions.RequestException as e:
            _logger.error("Request failed: %s", e)
            raise UserError(f"Request failed: {e}")

            

