from odoo import fields, models, _
import requests, json, datetime
from odoo.tools import config

class VkPosData(models.Model):

    _name = "vk.data"

    name = fields.Char("name", index=True)
    vendor = fields.Char("Vendor")
    items = fields.One2many('dummy.orders.line', 'vk_data_id', 'Order Lines')
    subtotal = fields.Float("Total")
    vat = fields.Float("VAT")
    total = fields.Float("Total(VAT included)")
    state = fields.Selection([('pending', 'PENDING'),
                              ('paid', 'PAID')], 'State',
                             default=lambda *a: 'pending')
    vkorder = fields.Boolean('Is vkOrder')
    is_cash = fields.Boolean('Is Cash Related')
    remark = fields.Char('Remark')
    partner_id = fields.Many2one('res.partner', 'Customer Name')



    def get_order(self, pid):
        data = self.search([('name','=',pid)],limit=1)
        print("=============", data, "======================")
        if data:
            items = []
            for item in data.items:
                items.append({
                    'name': item.product_id.name,
                    'unitPrice': item.product_id.list_price,
                    'qty': item.quantity,
                    'uom': item.uom,
                    'discount': item.discount,
                    'subtotal': item.subtotal
                })
            return {'purchaseId': pid,
                     'vendor': data.vendor,
                     'items': items,
                     'vkorder': data.vkorder,
                     'remark': data.remark,
                     'is_cash': data.is_cash,
                     'partner_id': data.partner_id.id or False,
                     'state':data.state,
                     'totalNoVat': data.subtotal,
                     'vat': data.vat,
                     'total': data.total
                     }
        else:
            return False



    def check_vk_status(self, pid):
        session = requests.Session()
        # get_param = self.env['ir.config_parameter'].sudo().get_param
        url = config['vkclub_api_url']
        client_id = config['vkclub_client_id']
        secret_key = config['vkclub_secret_key']




        res = requests.get(url + "/client_token", headers={
            "client_id": client_id,
            "secret_key": secret_key
        })
        print("hello from check vk status", res)
        if res.status_code != 200:
            # return
            raise Exception("error")
        # client_token = res.content
        print("res here =========== ", res)
        data = json.loads(res.content)
        client_token = data['clientToken']
        # print("This is the client_token", client_token)

        response = session.get(url + "/order_status" + "?order=" + str(pid), headers={
            "client_id": client_id,
            "client_token": client_token
        })
        print("hello", response)
        if response.status_code != 200:
            return False
        # vals = response.json()
        if res.request.body is None:
            data = self.search([('name', '=', pid)], limit=1)
            partner_id = False
            remark = False
            if data:
                print("reach data shit here", partner_id)
                data.write({
                    'state': 'paid',
                    'partner_id': partner_id,
                    'remark': remark,
                })
            return True
        return False


    def get_order_v7(self, cr, uid, id, pid, context=None):
        self.check_vk_status(cr, uid, id, pid, context)
        return self.get_order(cr, uid, id, pid, context)


    def get_order(self, pid):
        data = self.search([('name', '=', pid)], limit=1)
        print("=============", data.is_cash, "======================")
        if data:
            items = []
            for item in data.items:
                items.append({
                    'name': item.product_id.name,
                    'unitPrice': item.product_id.list_price,
                    'qty': item.quantity,
                    'uom': item.uom,
                    'discount': item.discount,
                    'subtotal': item.subtotal
                })
            return {'purchaseId': pid,
                    'vendor': data.vendor,
                    'items': items,
                    'vkorder': data.vkorder,
                    'remark': data.remark,
                    'is_cash': data.is_cash,
                    'partner_id': data.partner_id.id or False,
                    'state': data.state,
                    'totalNoVat': data.subtotal,
                    'vat': data.vat,
                    'total': data.total
                    }
        else:
            return False


    def set_order(self, data):
        self.set_order_model(data)


    def set_order_model(self, data):
        def is_change(rec, data):
            print("this is the data", data)
            if rec.total != data['total']:
                return True
            else:
                if rec.is_cash != data['is_cash']:
                    return True
                elif rec.state != data['state']:
                    return True
                elif data.get("vkorder", False) and rec.vkorder != data['vkorder']:
                    return True
            return False

        pid = data.get("purchaseId", False)
        if not pid:
            return False
        rec = self.search([("name", "=", pid)], limit=1)
        product_obj = self.env['product.template']
        orderlines = []
        for item in data['items']:
            item_name = ''
            if item['name']:
                for char in item['name']:
                    if char != '(':
                        item_name += char
                    else:
                        item['name'] = item_name[:-1]
                        break

            product = product_obj.search([('name', '=', item['name'])], limit=1)
            print("This is the product", product)
            orderlines.append([0, False, {'product_id': product.id,
                                          'quantity': item['qty'],
                                          'uom': item['uom'],
                                          'unit_price': item['unitPrice'],
                                          'discount': item['discount'],
                                          'subtotal': item['subtotal']}])
        print("rec", rec.total, data['total'])
        if rec:
            if (rec.state == 'pending') and is_change(rec, data):
                for line in rec.items:
                    line.unlink()
                rec.write({'vendor': data['vendor'],
                           'name': data['purchaseId'],
                           'vkorder': data.get("vkorder", False),
                           'remark': data.get("remark", False),
                           'state': data['state'],
                           'is_cash': data['is_cash'],
                           'partner_id': data.get("partner_id", False),
                           'items': orderlines,
                           'subtotal': data['totalNoVat'],
                           'vat': data['vat'],
                           'total': data['total']
                           })

        else:
            self.create({'vendor': data['vendor'],
                         'name': data['purchaseId'],
                         'vkorder': data.get("vkorder", False),
                         'remark': data.get("remark", False),
                         'state': data['state'],
                         'is_cash': data['is_cash'],
                         'partner_id': data.get("partner_id", False),
                         'items': orderlines,
                         'subtotal': data['totalNoVat'],
                         'vat': data['vat'],
                         'total': data['total']
                         })

    def create_vkorder(self, data):
        print("This is the data", data)
        id = self.search([("name", "=", 1)], limit=1)
        self.create_vkorder_model(data)

    def create_vkorder_model(self, data):
        product_obj = self.env['product.product']
        orderlines = []
        for item in data['items']:
            product = product_obj.search([('name', '=', item['name'])], limit=1)
            orderlines.append([0, False, {'product_id': product.id,
                                          'quantity': item.get("qty", 1),
                                          'uom': item.get("uom", ''),
                                          'unit_price': item.get("unitPrice", product.list_price),
                                          'discount': item.get("discount", 0),
                                          'subtotal': item.get("subtotal", product.list_price)}])
        self.env['vk.pos.order'].create({'vendor': data['vendor'],
                                     'name': data['purchaseId'],
                                     'remark': data.get("remark", False),
                                     'state': 'paid',
                                     'items': orderlines,
                                     'subtotal': data['totalNoVat'],
                                     'vat': data['vat'],
                                     'total': data['total']
                                     })

    def check_payment_method(self, oid):
        session = requests.Session()
        url = config['vkclub_api_url']
        client_id = config['vkclub_client_id']
        secret_key = config['vkclub_secret_key']
        # cookie = config['cookie']

        res = requests.get(url + "/client_token", headers={
            "client_id": client_id,
            "secret_key": secret_key,
            # "cookie": cookie
        })
        print("RES ========", dir(res))
        print("Status ====", res.status_code)
        print("RES content ===", res.content)
        if res.status_code != 200:
            raise Exception("error")
        # client_token = res.content
        data = json.loads(res.content)
        client_token = data['clientToken']

        response = session.get(url + "/order_status" + "?order=" + str(oid), headers={
            "client_id": client_id,
            "client_token": client_token,
            # "cookie": cookie
        })
        print("hello", response)
        if response.status_code != 200:
            return False
        vals = json.loads(response.content)
        print("VALS =======", vals)
        if vals:
            return vals
        return False
