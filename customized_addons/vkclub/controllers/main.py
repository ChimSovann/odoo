import odoo
import json
from odoo import http, fields
from odoo.http import request
from odoo.addons.req_res_handling.response import (
    valid_response, invalid_response)
from odoo.addons.vkclub.token import validate_token


class VkclubController(http.Controller):

    @http.route('/orders/delete_journal', type="http", auth="none", methods=["POST"], csrf=False)
    def delete_journal(self, **payload):
        if not payload:
            payload = json.loads(request.httprequest.data)
        journal_id = payload.get('journal_id', False)
        if journal_id:
            move_obj = request.env['account.move'].sudo()
            move_id = move_obj.search([('id', '=', journal_id)])
            move_id.button_cancel()
            move_id.unlink()
            return valid_response(data='success', status=200)
        else:
            return invalid_response(type="Fail Delete Journal",
                                    message="Fail Delete Journal!", status=401)

    @http.route('/orders/expire', type="http", auth="none", methods=["POST"], csrf=False)
    def create_revenue_journal(self, **payload):
        if not payload:
            payload = json.loads(request.httprequest.data)
        if not payload:
            payload = json.loads(request.httprequest.data)
        amount = payload.get('amount', False)
        partner_id = payload.get('partner_id', False)
        remark = payload.get('remark', False)
        if isinstance(amount, bool) and not amount:
            return invalid_response(type="Fail to Create Revenue Journal",
                                    message="Fail to Create Revenue Journal!", status=401)
        print("fuck you from order expire")
        if partner_id:
            print("helllloooooo from order expire")
            partner_obj = request.env['res.partner'].sudo(
            ).with_context(mail_create_nosubscribe=True)
            move_obj = request.env['account.move'].sudo(
            ).with_context(mail_create_nosubscribe=True)
            move_line_obj = request.env['account.move.line'].sudo().with_context(mail_create_nosubscribe=True,
                                                                                 check_move_validity=False)

            if isinstance(partner_id, dict):
                name = partner_id.get("first_name", "") + \
                " " + partner_id.get("last_name", "")
                query = """
                INSERT INTO res_partner(name, email) VALUES (%s, %s) RETURNING id;
                """
                request.cr.execute(query, (name, partner_id.get("email", '')))
                partner_id = request.cr.fetchall()[0][0]


            print(
                "===================== successfully creating partner object =========================")

            period_date = fields.Date.today()

            # testing server
            # 210006 - Cashpoint (deferred income)
            # debit_acc = 1908

            # Other Revenue Journal
            journal_id = 323

            # 210003 - Deferred Income - vKpoint
            debit_acc = 26480

            # 403003 - Other Income
            credit_acc = 26561

            # 200002 - VAT Output
            tax_acc = 26473

            move_vals = {
                'name': '/',
                'date': period_date,
                'state': 'draft',
                'type': 'entry',
                'currency_id': 2,
                'ref': "vkPoint Transaction Expire: " + remark,
                'journal_id': journal_id,
            }
            move_id = move_obj.create(move_vals)

            vals = {
                'name': remark,
                'ref': '/',
                'move_id': move_id.id,
                'account_id': debit_acc,
                'debit': amount,
                'credit': 0.0,
                'journal_id': journal_id,
                'date': period_date,
                'partner_id': partner_id,
            }
            move_line_obj.create(vals)
            cre_amount = round(amount / 1.1, 2)
            move_line_obj.create({
                'name': remark,
                'ref': '/',
                'move_id': move_id.id,
                'account_id': credit_acc,
                'credit': cre_amount,
                'debit': 0.0,

                'journal_id': journal_id,
                'date': period_date,
                'partner_id': partner_id,
            })
            move_line_obj.create({
                'name': remark,
                'ref': '/',
                'move_id': move_id.id,
                'account_id': tax_acc,
                'credit': amount - cre_amount,
                'debit': 0.0,

                'journal_id': journal_id,
                'date': period_date,
                'partner_id': partner_id,
            })
            move_id.action_post()
            return valid_response({
                'partner_id': partner_id,
                'journal_id': move_id.id
            })
        else:
            return invalid_response(type="Fail to Create Revenue Journal",
                                    message="Fail to Create Revenue Journal!", status=401)

    @validate_token
    @http.route('/orders/topup_delete', type="http", auth="none", methods=["POST"], csrf=False)
    def remove_top_up_journal(self, **payload):
        if not payload:
            payload = json.loads(request.httprequest.data)
        remark = payload.get('remark', False)
        cash_out = payload.get('cash_out', False)
        s = cash_out and "vkPoint Cash-out: " or "vkPoint Top-up: "
        move_obj = request.env['account.move'].sudo()
        if remark:
            try:
                moves = move_obj.search(["ref", "=", remark])
                for move in moves:
                    move.button_cancel()
                    move.unlink()
                return valid_response("success")
            except:
                pass
        return invalid_response(type="Fail to Remove Payment Journal",
                                message="Fail to Remove Payment Journal!", status=401)

    @validate_token
    @http.route('/orders/topup', type="http", auth="none", methods=["POST"], csrf=False)
    def create_top_up_journal(self, **payload):
        if not payload:
            payload = json.loads(request.httprequest.data)
        amount = payload.get('amount', False)
        debit_acc = payload.get('account_id', False)
        journal_id = payload.get('journal_id', False)
        partner_id = payload.get('partner_id', False)
        remark = payload.get('remark', False)
        cash_out = payload.get('cash_out', False)
        print(amount, partner_id)
        if amount and partner_id:
            partner_obj = request.env['res.partner'].sudo(
            ).with_context(mail_create_nosubscribe=True)
            move_obj = request.env['account.move'].sudo(
            ).with_context(mail_create_nosubscribe=True)
            move_line_obj = request.env['account.move.line'].sudo().with_context(
                mail_create_nosubscribe=True, check_move_validity=False)

            if isinstance(partner_id, dict):
                name = partner_id.get("first_name", "") + \
                    " " + partner_id.get("last_name", "")
                query = """
                INSERT INTO res_partner(name, email) VALUES (%s, %s) RETURNING id;
                """
                request.cr.execute(query, (name, partner_id.get("email", '')))
                partner_id = request.cr.fetchall()[0][0]
                

            print(
                "===================== successfully creating partner object =========================")

            period_date = fields.Date.today()

            if debit_acc:
                debit_acc = int(debit_acc)
            else:
                return invalid_response(type="Fail to Create Payment Journal",
                                        message="Debit Account Not Fount!", status=401)

            if journal_id:
                journal_id = int(journal_id)
            else:
                return invalid_response(type="Fail to Create Payment Journal",
                                        message="Journal ID Not Fount!", status=401)

            # 403003 - Other Income
            credit_acc = 26480

            # reverse account for cash out
            if cash_out:
                debit_acc, credit_acc = credit_acc, debit_acc

            s = cash_out and "vkPoint Cash-out: " or "vkPoint Top-up: "

            move_vals = {
                'state': 'draft',
                'type': 'entry',
                'currency_id': 2,
                'date': period_date,
                'ref': remark,
                'journal_id': journal_id,
                'company_id': 13
            }

            print("===================== successfully nearly creating move val object =========================", partner_id)

            move_id = move_obj.create(move_vals)
            print("This is the move_id", move_id)
            print(
                "===================== successfully creating move val object =========================")
            vals = {
                'name': s+remark,
                'ref': '/',
                'move_id': move_id.id,
                'account_id': debit_acc,
                'debit': amount,
                'credit': 0.0,
                'journal_id': journal_id,
                'date': period_date,
                'partner_id': partner_id,
            }
            move_line_obj.create(vals)
            print(
                "===================== successfully creating vals object =========================")
            move_line_obj.create({
                'name': s+remark,
                'ref': '/',
                'move_id': move_id.id,
                'account_id': credit_acc,
                'credit': amount,
                'debit': 0.0,
                'journal_id': journal_id,
                'date': period_date,
                'partner_id': partner_id,
            })
            print(
                "===================== successfully creating idk object =========================")

            move_id.action_post()
            print(
                "===================== successfully creating lmfao object =========================")
            return valid_response({
                'partner_id': partner_id,
                'journal_id': move_id.id
            })
        else:
            return invalid_response(type="Fail to Create Payment Journal",
                                    message="Fail to Create Payment Journal!", status=401)

    @validate_token
    @http.route('/orders/commit', type="http", auth="none", methods=["POST"], csrf=False)
    def commit_order(self, **payload):
        # Change order status to paid
        print(1)
        partner_obj = request.env['res.partner'].sudo(
        ).with_context(mail_create_nosubscribe=True)
        registry, cr, context = request.registry, request.cr, request.context
        print(2)
        if not payload:
            payload = json.loads(request.httprequest.data)
        print(3)
        pid = payload.get("purchaseId", False)
        partner_id = payload.get("partner_id", False)
        print(3.1)
        if isinstance(partner_id, dict):
            name = partner_id.get("first_name", "") + \
                " " + partner_id.get("last_name", "")
            query = """
            INSERT INTO res_partner(name, email) VALUES (%s, %s) RETURNING id;
            """
            request.cr.execute(query, (name, partner_id.get("email", '')))
            partner_id = request.cr.fetchall()[0][0]
            

        if not pid:
            return invalid_response(type="Invalid OID", message="Could not find your OID", status=401)
        purchaseId = pid
        vkdata_obj = request.env['vk.data'].sudo()
        data = vkdata_obj.get_order(purchaseId)
        remark = ''
        print("Hello this is 6", data)
        if payload.get('remark', False):
            remark = payload['remark']

        if data and data['state'] != 'paid':
            print("Hello from 326")
            if vkdata_obj.check_vk_status(purchaseId):
                print("Hello from 328", partner_id)
                data.update({
                    'state': 'paid',
                    'remark': remark,
                    'partner_id': partner_id,
                })
                print(5)
                registry["vk.pos.order"].post(request, data=data)
                print(6)
                print("Thissssss")
                print(data)
                request.env['vk.data'].sudo().set_order_model(data)
                # Noncash Data
                if data.get('vkorder', False):
                    request.env['vk.data'].sudo().create_vkorder_model(data)
                return valid_response({
                    'partner_id': partner_id,
                })
        return invalid_response(type="Fail to Commit", message="Cannot find your order! Your Order maybe already PAID",
                                status=401)

    @validate_token
    @http.route('/orders/info/<string:pid>', type="http", auth="none", methods=["GET"], csrf=False)
    def get_order_info(self, pid, **payload):
        purchaseId = pid.split('-')
        print("hello from 348")
        vender = "Moringa"
        if purchaseId[0] == 'PID':
            print("hello from 351")
            products = request.env['product.template'].sudo().search(
                [('vkpoint_ref', '=', purchaseId[1])])
            if not products:
                return invalid_response(type="Invalid PID", message="Could not find your PID", status=401)
            items = []
            total = 0
            id = request.env['ir.sequence'].sudo().get('vk.order.sequence')
            for product in products:
                total += product.list_price
                
                items.append({
                    'name': product.name.split("'"),
                    'uom': product.uom_id.name or "",
                    'unitPrice': product.list_price,
                    # 'imageURL': str(request.env['ir.config_parameter'].get_param('web.base.url'))+'/web/binary/image?model=product.product&field=image_medium&id='+str(product.id),
                    'qty': 1,
                    'discount': 0.0,
                    'subtotal': product.list_price
                })
               

            data = {'purchaseId': 'OID-' + id,
                    'vendor': vender,
                    'items': items,
                    'vkorder': True,
                    'state': 'pending',
                    'is_cash': False,
                    'totalNoVat': round(total, 2),
                    'vat': 0.0,
                    'total': round(total, 2)
                    }
            request.env['vk.data'].sudo().set_order_model(data)

            return valid_response(data)

        elif purchaseId[0] == 'OID':
            print("hello from 391")
            order = request.env['vk.data'].sudo().get_order(pid)
            print("hello from 392", order)
            if not order:
                return invalid_response(type="Invalid OID", message="Could not find your OID", status=401)

            return valid_response(order)

        return invalid_response(type="Invalid Request", message="Could not execute your request", status=401)
