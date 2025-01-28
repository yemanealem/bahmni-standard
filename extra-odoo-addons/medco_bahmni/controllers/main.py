from odoo import http
from odoo.http import request, Response
import json
import logging
from odoo.exceptions import UserError
from werkzeug.utils import redirect  # Import the redirect function
_logger = logging.getLogger(__name__)

class PaymentController(http.Controller):

    @http.route('/confirm-payment/post', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_post_request(self, **post_data):
        _logger.info("Received POST request to confirm payment")
        
        try:
            # Parse the incoming data
            data = json.loads(request.httprequest.data.decode('utf-8'))
            transaction_no = data.get('trans_no')
            transaction_date = data.get('trans_date')
            transaction_id = data.get('id')
            checkout_url =data.get('checkout_url')
            
            if not transaction_no or not transaction_date:
                return Response(
                    json.dumps({"error": "Missing required fields (transaction No, transaction date)"}),
                    status=400
                )
            

            account_move = request.env['account.move'].sudo().search([('id', '=', transaction_id)], limit=1)
            if account_move:
                account_move.write({'transaction_no': transaction_no,'checkout_url':checkout_url, 'trans_timestamp': transaction_date})
            else:
                return Response(
                    json.dumps({"error": "Account move not found"}),
                    status=404
                )

            _logger.info("Account move updated successfully")

            

        except Exception as e:
            _logger.error("Error processing the request: %s", str(e))
            return Response(
                json.dumps({"error": str(e)}),
                status=500
            )

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
