from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import requests
import uuid
import time

_logger = logging.getLogger(__name__)

temp_checkout_urls = {}

class AccountMove(models.Model):
    _inherit = 'account.move'

    transaction_no = fields.Char('Transaction No')
    trans_timestamp = fields.Date('Transaction Timestamp')
    checkout_url = fields.Char(string="checkout_url")
    # phone=fields.Char('phone')
    eligibility = fields.Char(string="Eligibility", default="Not Checked Yet!")


    def send_payment(self):

        # Only Authenticated  must be match to do 

        products = [line.product_id.name for line in self.invoice_line_ids]
        _logger.info("Invoice Data: %s",products)

        odo_api_url = "http://192.168.226.77:8069"
        callback_checkout_url = f"{odo_api_url}/checkout-payment/post"
        payment_verification_url = f"{odo_api_url}/confirm-payment/post"

        openFn_api_url = "http://192.168.226.131:4000/i/64f19725-e4cd-46d7-8399-037b467ce164"
        merchant_id='12738'
        return_url='http://localhost:8069/web#action=244&model=account.move&view_type=list&cids=1&menu_id=121'
        api_key='CHASECK-EKqvJrN99dictFBV8MaL9OIUymw9nozc'

        transaction_no = f"{self.id}-{uuid.uuid4().hex[:8]}"  
        payinfo = {
            'move_id': self.id,
            'move_name': self.name,
            'amount': 3,
            'date': self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else None,  
            'cust_id': self.partner_id.id,
            'first_name': self.partner_id.name.split()[0],
            'last_name':" ".join(self.partner_id.name.split()[1:]),
            'tx_ref': transaction_no,
            'email': self.partner_id.email or '',
            'phone_number': self.partner_id.phone or '',
            'callback_checkout_url':callback_checkout_url,
            'payment_verification_url':payment_verification_url,
            'serviceName': products,
            'title':self.partner_id.title or '',
            'merchant_id': merchant_id,
            'hideReceipt': False,
            'providerName': 'Alert hospital',
            'return_url': return_url,
            'api_key': api_key
     
        }



        _logger.info("Sending data to API: %s", payinfo)

        try:
            response = requests.post(openFn_api_url, json=payinfo, timeout=100)
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



    def action_custom_button(self,data):
         _logger.info("Received callback data: %s", data)

                 

    def check_eligibility(self):

        
        cbhi_data = {
        'move_id': self.id,
        'move_name': self.name,
        'amount': self.amount_total,
        'date': self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else None,  
        'cust_id': self.partner_id.id,
        'first_name': self.partner_id.name,
        'email': self.partner_id.email or '',
        'phone_number': self.partner_id.phone or '',
        'cbhiId':self.partner_id.cbhiId or '',
        'hospital_name': self.partner_id.company_id.name if self.partner_id.company_id else 'ZEWDITU',  

        'products': [{
            'product_id': line.product_id.id,
            'product_name': line.product_id.name,
            'quantity': line.quantity,
            'price_unit': line.price_unit,
            'subtotal': line.price_subtotal
        } for line in self.invoice_line_ids] }


        # _logger.info("Received data from the elegibility: %s",  cbhi_data)


        # base_url = "http://cbhi.medcoanalytics.com/api/cbhi/insured/check-eligibility"
        base_url="http://192.168.210.196:8900/api/cbhi/insured/check-eligibility"
        params = {
            "Search": self.partner_id.cbhiId or '' ,
            "page": 1,
            "limit": 25
        }


        try:
            _logger.info("deta sent for eligibility check : %s",params)

            response = requests.get(base_url, params=params, timeout=100)
            response_data = response.json()  
            _logger.info("response data from CBHI: %s", response_data)

            if response.ok and "response" in response_data and isinstance(response_data["response"], list) and response_data["response"]:
               
                cbhi_id = response_data["response"][0].get("cbhiId")
                phone_number=response_data["response"][0].get("phoneNumber")
                message = f"✅ The patient is CBHI Insured. With CBHI ID: {cbhi_id}"


                self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {'message': message})

                res_partner = self.env['res.partner'].sudo().search([('phone', '=',phone_number )], limit=1)
                res_partner.write({'cbhiId': cbhi_id})


                account_move = self.env['account.move'].sudo().search([('id', '=', self.id)], limit=1)
                if account_move:
                    account_move.write({'eligibility': "Eligible"})
                    claim_data = {
                    
                    'amount': cbhi_data.get('amount', 0.0),
                    'date': cbhi_data.get('date'),
                    'cbhi_id': cbhi_id,
                    'state': 'draft', 
                    'partner_id': cbhi_data.get('cust_id'),
                    'invoice_id': cbhi_data.get('move_id'),
                    'hospital_name':'ZEWDITU'
                }

                claim = self.env['account.claim'].create(claim_data)

                claim_line_vals = []
               
                for product in cbhi_data.get('products', []):
                    claim_line_vals.append((0, 0, {
                        'product_id': product['product_id'],
                        'quantity': product['quantity'],
                        'price_unit': product['price_unit'],
                        'subtotal': product['subtotal'],
                    }))

                _logger.info("Received data from the eligibility check: %s", claim_line_vals)
    

                if claim_line_vals:
                    claim.sudo().write({'claim_line_ids': claim_line_vals})       


            else:
                _logger.error("User not Insured")
                message = "❌ The Patient is not CBHI insured,Pay with Chapa"
                
                account_move = self.env['account.move'].sudo().search([('id', '=', self.id)], limit=1)

                account_move.write({'eligibility': "Not Eligible"})

                self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {'message': message,'duration': 5000})

            
        except requests.exceptions.Timeout:
            _logger.error("Request timed out. The server took too long to respond.")
            raise UserError("Request timed out. Please try again later.")
        except requests.exceptions.RequestException as e:
            _logger.error("Request failed: %s", e)
            raise UserError(f"Request failed: {e}")



    def open_direct_pay_modal(self):
        return {
            'name': 'Direct Pay',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': self.env.ref('medco_bahmni.view_direct_pay_modal').id,
            'type': 'ir.actions.act_window',
            'target': 'new',  
            'context': {'default_move_id': self.id},  
        }
    

    def direct_pay(self):
        _logger.info("Direct Pay initiated for Invoice ID: %s", self.id)
        
        try:
            _logger.info("Payment process started for invoice: %s", self.id)
            return {
                'type': 'ir.actions.act_window_close', 
            }
        except Exception as e:
            _logger.error("Error processing payment: %s", e)
            raise UserError(f"Error processing payment: {e}")