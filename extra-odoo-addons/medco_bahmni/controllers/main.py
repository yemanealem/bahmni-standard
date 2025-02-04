from odoo import http
from odoo.http import request, Response
import json
import logging
import hmac
import hashlib
import base64
import json
import logging
from odoo.exceptions import UserError
from werkzeug.utils import redirect  # Import the redirect function
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
        

    def _handle_successful_payment(self, data):
        _logger.info("✅ Payment Successful: %s", data)

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            transaction_no = data.get('tx_ref')
            _logger.info("✅ transaction number: %s", transaction_no)


            if not transaction_no:
                return Response(json.dumps({"error": "Missing required fields"}), status=400)

            account_move_update = request.env['account.move'].sudo().search([('transaction_no', '=', transaction_no)])
            if not account_move_update.exists():
                return Response(json.dumps({"error": "Account move not found"}), status=404)

            account_move_update[0].sudo().write({
                'transaction_no': transaction_no,
                'payment_state': 'paid'
            })


           
 
            # response = requests.post(openFn_api_url, json=data, timeout=100)




            return Response(json.dumps({"success": "Payment confirmed"}), status=200)

        except Exception as e:
            _logger.error("Error processing request: %s", str(e))
            return Response(json.dumps({"error": str(e)}), status=500)



    def _handle_failed_payment(self, payload):
        
         return Response(json.dumps({"success": "Payment confirmed"}), status=200)


    def _handle_refunded_payment(self, payload):
        
        return Response(json.dumps({"success": "Payment confirmed"}), status=200)


    def _handle_reversed_payment(self, payload):

        _logger.info("Reversed callled: %s", payload)

        
        return Response(json.dumps({"success": "Payment confirmed"}), status=200)


    def _handle_successful_payout(self, payload):

        return Response(json.dumps({"success": "Payment confirmed"}), status=200)


    def _handle_failed_payout(self, payload):

        return Response(json.dumps({"success": "Payment confirmed"}), status=200)

    

    @http.route('/confirm-payment/post', type='json', auth='none', methods=['POST'], csrf=False)
    def handle_post_request(self, **post_data):
        # api_key = request.httprequest.headers.get('Authorization')
        
        # api_key = api_key.split("Bearer ")[1] 
        # _logger.info("the token is : %s", api_key)

        # auth_api = self.auth_api_key(api_key)

        # if auth_api != True:
        #     return auth_api

        # user = request.env['res.users'].sudo().search([('api_key_ids', '=', api_key)])
        # if not user:
        #     return Response(json.dumps({"error": "Invalid API key"}), status=403)

        # request.uid = user.id  
        # _logger.info(f"Authenticated user: {user.name} (ID: {user.id})")


        chapa_signature = request.httprequest.headers.get('x-chapa-signature')

        data = json.loads(request.httprequest.data.decode('utf-8'))


        if not chapa_signature or not self._verify_signature(data, chapa_signature):
            return {'status': 'error', 'message': 'Invalid signature'}, 401
        

        event_type = data.get('event')
        _logger.info("Event data: %s", event_type)


        if event_type == "charge.success":
            
            _logger.info("Entered to Suceess: %s", event_type)

            self._handle_successful_payment(data)
        elif event_type == "charge.failed":
            self._handle_failed_payment(data)
        elif event_type == "charge.refunded":
            self._handle_refunded_payment(data)
        elif event_type == "charge.reversed":
           
            _logger.info("Entered to Suceess: %s", event_type)

            self._handle_reversed_payment(data)
        elif event_type == "payout.success":
            self._handle_successful_payout(data)
        elif event_type == "payout.failed":
            self._handle_failed_payout(data)
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
