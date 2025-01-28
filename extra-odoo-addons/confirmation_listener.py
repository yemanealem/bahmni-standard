from odoo import http
from odoo.http import request, Response
import json
import logging
_logger = logging.getLogger(__name__)



class CustomPostController(http.Controller):

    @http.route('/custom/post', type='http', auth='public', methods=['POST'], csrf=False)
    def handle_post_request(self, **post_data):
        _logger.info("recived post Request")

        try:
            #Add authentication
            id = post_data.get('id')
            transaction_no=post_data.get('trans_no')
            transaction_date=post_data.get('trans_date')

            if not transaction_no or not transaction_date:
                return Response(json.dumps({"error": "Missing required fields (transaction No, transaction date)"}), status=400)

            account_move_update = request.env['account.move'].search(['id','=',id])
            account_move_update[0].write({'transaction_no': transaction_no,'trans_timestamp':transaction_date})

            return Response(json.dumps({
                "status": "success",
                "message": "Record updated successfully",
            }), status=200)

        except Exception as e:
            return Response(json.dumps({"error": str(e)}), status=500)
