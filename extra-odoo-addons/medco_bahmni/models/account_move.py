from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import requests
import uuid
import time

_logger = logging.getLogger(__name__)

# Dictionary to store checkout URLs temporarily (Key: record ID)
temp_checkout_urls = {}

class AccountMove(models.Model):
    _inherit = 'account.move'

    transaction_no = fields.Char('Transaction No')
    trans_timestamp = fields.Date('Transaction Timestamp')
    checkout_url = fields.Char(string="checkout_url")

    def send_payment(self):

        # Authentication Header

        api_url = "http://192.168.100.82:4000/i/64f19725-e4cd-46d7-8399-037b467ce164"

        transaction_no = f"{self.id}-{uuid.uuid4().hex[:8]}"  
        payinfo = {
            'move_id': self.id,
            'move_name': self.name,
            'amount': self.amount_total,
            'date': self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else None,  
            'cust_id': self.partner_id.id,
            'first_name': self.partner_id.name,
            'tx_ref': transaction_no,
            'email': self.partner_id.email or '',
            'phone_number': self.partner_id.phone or '',
            'callback_url': 'http://192.168.100.34:8069/checkout-payment/post',
        }

        _logger.info("Sending data to API: %s", payinfo)

        try:
            response = requests.post(api_url, json=payinfo, timeout=100)
            _logger.info("API response: %s", response.status_code)

            if response.status_code != 200:
                raise UserError(f"Error: Payment request failed with status code {response.status_code}")

            retries = 10
            while retries > 0:
                checkout_url = temp_checkout_urls.get(self.id)  
                redirect_to=checkout_url
                temp_checkout_urls.clear()

                
                if checkout_url:
                    _logger.info("Updated URL found: %s", redirect_to)
                    return {
                        'type': 'ir.actions.act_url',
                        'url': redirect_to,
                        'target': 'new',
                    }

                _logger.info("Checkout URL not available, retrying... (%d retries left)", retries)
                time.sleep(8)
                retries -= 1

            raise UserError("Request Timeout: please check your internet connection and   try agian")

        except requests.exceptions.RequestException as e:
            raise UserError(f"Request failed: {e}")

    def send_payment_with_data(self, data):
        _logger.info("Received callback data: %s", data)

        checkout_url = data.get('checkout_url')
        if checkout_url:
            temp_checkout_urls[self.id] = checkout_url  # Store in dictionary
            _logger.info("Checkout URL updated successfully: %s", checkout_url)
