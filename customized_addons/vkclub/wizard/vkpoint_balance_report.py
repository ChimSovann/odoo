from odoo.exceptions import except_orm, ValidationError
from odoo import models, fields, api, _
import requests, json
from odoo.tools import config

class vk_balance(models.TransientModel):
    _name = "vkpoint.balance"

    start_date = fields.Date('Start Date', default=fields.Date.context_today)
    end_date = fields.Date('End Date', default=fields.Date.context_today)
    type = fields.Selection(string='Transaction Type',
                            default='cash',
                            selection=[
                                ('cash_top_up', 'Cash Top-up'),
                                ('cash_payment', 'Cash Payment'),
                                ('cash', 'Cash'),
                                ('noncash', 'Non-Cash'),
                                ('all', 'All')])
    partner_id = fields.Many2one('res.partner', string='User',domain=[('last_name', 'ilike', '00%')])


    def get_month_balance(self):

        get_param = self.env['ir.config_parameter'].get_param
        url = config['vkclub_api_url']
        client_id = config['vkclub_client_id']
        secret_key = config['vkclub_secret_key']

        res = requests.get(url + "/client_token", headers={
            "client_id": client_id,
            "secret_key": secret_key
        })
        if res.status_code != 200:
            raise Exception("error")
        data = json.loads(res.content)
        client_token = data['clientToken']

        response = requests.get(url + "/memberships/month_report_cash", headers={
            "client_id": client_id,
            "client_token": client_token
        })
        if response.status_code != 200:
            raise Exception("error")
        vals = response.json()
        non_obj = self.env['vkpoint.account.month.report.cash']
        print("------------------------stop==month_report_cash===", vals)
        for val in vals:
            if val.get("current", False):
                res = non_obj.search([('name', '=', val.get("name", False)),
                                   ('membership_name', '=', val.get("membership_name", False))])
                try:
                    res.write({"balance_end": val.get("balance_end", False)})
                except:
                    pass
            else:
                non_obj.create({
                    "name": val.get("name", False),
                    "date": val.get("date", False),
                    "balance_start": val.get("balance_start", False),
                    "balance_end": val.get("balance_end", False),
                    "membership_name": val.get("membership_name", False),
                })

        response = requests.get(url + "/memberships/month_report_noncash", headers={
            "client_id": client_id,
            "client_token": client_token
        })
        if response.status_code != 200:
            raise Exception("error")
        vals_non = response.json()
        non_obj = self.env['vkpoint.account.month.report.noncash']
        print("------------------------stop=month_report_noncash====", vals_non)
        for val in vals_non:
            if val.get("current", False):
                res = non_obj.search([('name', '=', val.get("name", False)),
                                      ('membership_name', '=', val.get("membership_name", False))])
                try:
                    res.write({"balance_end": val.get("balance_end", False)})
                except:
                    pass
            else:
                non_obj.create({
                    "name": val.get("name", False),
                    "date": val.get("date", False),
                    "balance_start": val.get("balance_start", False),
                    "balance_end": val.get("balance_end", False),
                    "membership_name": val.get("membership_name", False),
                })


    def get_all_transaction(self):
        print("-------Getting All Transaction-------=")
        cash_obj = self.env['vk.point.transaction.cash']
        noncash_obj = self.env['vk.point.transaction.noncash']
        # gg = self.search([])
        # gh = cash_obj.search([])
        # for g in gg:
        #     g.unlink()
        # for g in gh:
        #     g.unlink()
        # print "------------------------stop====="

        url = config['vkclub_api_url']
        client_id = config['vkclub_client_id']
        secret_key = config['vkclub_secret_key']

        res = requests.get(url + "/client_token", headers={
            "client_id": client_id,
            "secret_key": secret_key
        })
        if res.status_code != 200:
            raise Exception("error")
        data = json.loads(res.content)
        client_token = data['clientToken']
        response = requests.get(url + "/memberships/all_transaction", headers={
            "client_id": client_id,
            "client_token": client_token
        })
        if response.status_code != 200:
            raise Exception("error")
        vals = response.json()
        for val in vals:
            trsc_type = val.get("trsc_type", False)
            aa = bb =None
            if trsc_type in ('zpayment_cash', 'top_up'):
                bb = cash_obj.create({
                    "name": val.get("name", False),
                    "trsc_info": val.get("trsc_info", False),
                    "trsc_date": val.get("trsc_date", False),
                    "amount_cash": val.get("amount_cash", False),
                    "remark": val.get("remark", False),
                    "membership_id": val.get("membership_id", False),
                    "membership_name": val.get("membership_name", False),
                    "payment_method": val.get("payment_method", False),
                    "ref_num": val.get("ref_num", False),
                    "trsc_type": trsc_type,
                    "expire_date": val.get("expire_date", False),
                })
            else:
                aa = noncash_obj.create({
                    "name": val.get("name", False),
                    "trsc_info": val.get("trsc_info", False),
                    "trsc_date": val.get("trsc_date", False),
                    "amount_noncash": val.get("amount_noncash", False),
                    "remark": val.get("remark", False),
                    "membership_id": val.get("membership_id", False),
                    "membership_name": val.get("membership_name", False),
                    "payment_method": val.get("payment_method", False),
                    "ref_num": val.get("ref_num", False),
                    "trsc_type": trsc_type,
                    "expire_date": val.get("expire_date", False),
                })

            print(aa, bb, "------------------------stop=====", trsc_type in ('zpayment_cash', 'top_up'))


    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'vk.pos.order',
            'form': self.read(['start_date', 'end_date', 'type', 'partner_id'])[0]
        }
        print(data['form'], 'this is data form')

        url = config['vkclub_api_url']
        client_id = config['vkclub_client_id']
        secret_key = config['vkclub_secret_key']

        res = requests.get(url + "/client_token", headers={
            "client_id": client_id,
            "secret_key": secret_key
        })
        if res.status_code != 200:
            raise Exception("error")
        # change client token
        data_res = json.loads(res.content)
        client_token = data_res['clientToken']
        partner_id = data["form"]["partner_id"]
        if partner_id:
            partner_id = partner_id[1].split(' ')[-1]
        param = "?type="+str(data["form"]["type"])+"&membership_id="+str(partner_id)+"&start_date="+str(data["form"]["start_date"])+"&end_date="+str(data["form"]["end_date"])
        response = requests.get(url + "/memberships/report_transaction"+param, headers={
            "client_id": client_id,
            "client_token": client_token
        })
        if response.status_code != 200:
            raise Exception("error")
        vals = response.json()
        data["form"].update({
            "data": vals
        })
        transactions = self._get_details(data['form'])
        balance = self._get_start_balance(data['form'])
        transactions_ex = self._get_expire_details(data['form'])
        total = self._get_total(data['form'])

        datas = {
            'ids': self.ids,
            'model': 'vk.pos.order',
            'form': self.read(['start_date', 'end_date', 'type'])[0],
            'doc': vals,
            'transactions': transactions,
            'balance': balance,
            'transactions_ex': transactions_ex,
            'total': total
        }


        return self.env.ref('vkclub.vk_balance_report').report_action(self, data=datas)





    def _get_expire_details(self,form):
        data = form['data']["ex_transaction"]
        return data

    def _get_details(self,form):
        data = form['data']["transaction"]
        print(data)
        return data

    def _get_start_balance(self,form):
        data = form['data']["start_balance"]
        return data

    def _get_total(self, form):
        data = form['data']["total"]
        return data

    def _get_end_balance(self,form):
        data = form['data']["end_balance"]
        return data


