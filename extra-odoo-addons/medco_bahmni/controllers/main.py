from odoo import http
from odoo.http import request, Response
import json
import logging
import hmac
import hashlib
import base64
import json
import logging
import requests
from odoo.exceptions import UserError
from werkzeug.utils import redirect  
_logger = logging.getLogger(__name__)

class PaymentController(http.Controller):
    SECRET_KEY = "xndbjBn1238948394ftwqlritroplnm" 


    def auth_api_key(self, api_key):
    
        try:
            user_id = request.env['res.users'].sudo().search([('api_key_ids', '=', api_key)])
        except ValueError as e:
                return {"error": "Invalid field in query", "details": str(e)}, 400
        
        if api_key is not None and user_id:
            response = True
        elif not user_id:
            response = ('<html><body><h2>Invalid <i>API Key</i> '
                        '!</h2></body></html>')
        else:
            response = ("<html><body><h2>No <i>API Key</i> Provided "
                        "!</h2></body></html>")
        return response
    


    def _verify_signature(self, payload, chapa_signature):
        
        
        
        _logger.error("requested data payload: %s", payload)

    
        try:
            payload_string = json.dumps(payload, separators=(',', ':'))
            computed_signature = hmac.new(
                self.SECRET_KEY.encode(),
                payload_string.encode(),
                hashlib.sha256
            ).digest()
            computed_signature_base64 = base64.b64encode(computed_signature).decode()
            
            _logger.error("computed signiture: %s", computed_signature_base64)


            return computed_signature_base64 == chapa_signature
        except Exception as e:
            _logger.error("Signature verification failed: %s", e)
            return False
        


 
            # response = requests.post(openFn_api_url, json=data, timeout=100)


    def send_data_to_openFn(self, payload):


        
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            transaction_no = data.get('reference')
            _logger.info("✅ transaction number: %s", transaction_no)


            if not transaction_no:
                return Response(json.dumps({"error": "Missing required fields"}), status=400)

            try:
                account_move_update = request.env['account.move'].sudo().search([('transaction_no', '=', transaction_no)])
                
                if not account_move_update.exists():
                    _logger.info("Record does not exist for transaction_no: %s", transaction_no)
                else:
                    account_move_update[0].sudo().write({
                        'transaction_no': transaction_no,
                        'payment_state': 'paid'
                    })
                    _logger.info("Successfully updated account.move with transaction_no: %s", transaction_no)

            except IndexError:
                _logger.error("Index error: Attempted to access an empty recordset for transaction_no: %s", transaction_no)

            except Exception as e:
                _logger.error("An error occurred while updating account.move: %s", str(e), exc_info=True)

          
            openFn_api_url="http://192.168.210.131:4000/i/90360758-618c-4c77-8efd-e52d867ef5da"
    
            response = requests.post(openFn_api_url, json=payload, timeout=100)
            try:
                response = requests.post(openFn_api_url, json=payload, timeout=100)
                _logger.info("✅ transaction number: %s", response)

            except requests.Timeout:
                _logger.info("Error: The request timed out.")

            except requests.ConnectionError:
                _logger.info("Error: Failed to connect to the server.")

            except requests.HTTPError as http_err:
                _logger.info("Error: Failed to connect to the server:  %s",http_err)

            except requests.RequestException as req_err:
                print(f"An error occurred: {req_err}")
                _logger.info("Error: Failed to connect to the server:  %s",req_err)


        except Exception as e:
            _logger.error("Error processing the request: %s", str(e))
            return Response(
                json.dumps({"error": str(e)}),
                status=500
            )


    @http.route('/confirm-payment/post', type='json', auth='none', methods=['POST'], csrf=False)
    def handle_post_request(self, **post_data):
        

        chapa_signature = request.httprequest.headers.get('x-chapa-signature')

        _logger.info("CHapa Signiture: %s", chapa_signature)


        data = json.loads(request.httprequest.data.decode('utf-8'))

        # if not chapa_signature or not self._verify_signature(data, chapa_signature):
        #     return {'status': 'error', 'message': 'Invalid signature'}, 401
        

        event_type = data.get('event')
        _logger.info("Event data: %s", event_type)

        # message = f"✅ Payment Suceesfully"
        # self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {'message': message})

        if event_type == "charge.success":
            
            _logger.info("Entered to Suceess: %s", event_type)

            self.send_data_to_openFn(data)
            _logger.info("Returned after OPenFN")


            return Response(json.dumps({"success": "Payment confirmed"}), status=200)

        elif event_type == "charge.failed":

            self.send_data_to_openFn(data)
            _logger.info("Entered to failed: %s", event_type)
            return Response(json.dumps({"success": "Payment confirmed"}), status=200)

        elif event_type == "charge.refunded":
            _logger.info("Entered to refend: %s", event_type)
            self.send_data_to_openFn(data)
            return Response(json.dumps({"success": "Payment confirmed"}), status=200)


        elif event_type == "charge.reversed":
           
            _logger.info("Entered to reversed: %s", event_type)

            self.send_data_to_openFn(data)
            _logger.info("Entered to  after openFn: %s", event_type)

            return Response(json.dumps({"success": "Payment confirmed"}), status=200)


        elif event_type == "payout.success":

            self.send_data_to_openFn(data)
            _logger.info("Entered to  after openFn: %s", event_type)

            return Response(json.dumps({"success": "Payment confirmed"}), status=200)


        elif event_type == "payout.failed":
            self.send_data_to_openFn(data)
            _logger.info("Entered to  after openFn: %s", event_type)

            return Response(json.dumps({"success": "Payment confirmed"}), status=200)


            
        else:
            return {'status': 'error', 'message': f'Unknown event type: {event_type}'}, 400

        
    @http.route('/checkout-payment/post', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_checkout_request(self, **post_data):
        #Authentication Header should add in this 

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            transaction_no = data.get('trans_no')
            id = data.get('id')
            transaction_date = data.get('trans_date')
            checkout_url = data.get('checkout_url') 

            if not transaction_no or not transaction_date:
                return Response(
                    json.dumps({"error": "Missing required fields (transaction No, transaction date)"}),
                    status=400
                )
            account_move = request.env['account.move'].sudo().search([('id', '=', id)], limit=1)
            if account_move:
                 account_move.write({'transaction_no': transaction_no,'checkout_url':checkout_url, 'trans_timestamp': transaction_date})
           
            account_move.send_payment_with_data(data)
            
        except Exception as e:
            _logger.error("Error processing the request: %s", str(e))
            return Response(
                json.dumps({"error": str(e)}),
                status=500
            )


    @http.route('/bahmni/claim-update', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_update_claim_request(self, **post_data):

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            claim_id = data.get('claimUuid')
            status = data.get('status')

            if not claim_id:
                return Response(
                    json.dumps({"error": "Missing Claim Number"}),
                    status=400
                )
            

            update_claim = request.env['account.claim'].sudo().search([('claim_number', '=', claim_id)], limit=1)

            if update_claim:
                update_claim.write({'state': status})
                
                invoice_number = update_claim.invoice_id.name
                _logger.info("Invoice Number: %s", invoice_number)

                
                if invoice_number:
                    if status=='paid':
                        update_account_move = request.env['account.move'].sudo().search([('name', '=', invoice_number)], limit=1)
                        update_account_move.write({'payment_state': status})

                        _logger.info("Reversed called: %s", update_account_move)

                    
                    return Response(
                            json.dumps({"message": "Updated Successfully"}), 
                            status=200,  
                            content_type="application/json"
                        )

                
    
                else:
                    _logger.warning("Invoice ID not found for claim: %s", claim_id)
            else:
                _logger.warning("Claim not found for claim_number: %s", claim_id)

            
           
            
        except Exception as e:
            _logger.error("Error processing the request: %s", str(e))
            return Response(
                json.dumps({"error": str(e)}),
                status=500
            )
