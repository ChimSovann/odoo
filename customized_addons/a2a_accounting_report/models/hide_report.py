from odoo import fields, models, api

# For future requirement# For future requirement# For future requirement



class HideReport(models.Model):
  _inherit = "account.move"

  @api.model
  def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    res = super(HideReport, self).fields_view_get(
      view_id=view_id,
      view_type=view_type,
      toolbar=toolbar,
      submenu=submenu)

    report_names = {
      1: 'vKirirom Commercial Invoice',
      2: 'vKirirom Tax Invoice',
      3: 'A2A IT Service Commercial Invoice',
      4: 'A2A IT Service Tax Invoice',
      5: 'Commercial Invoice Jobify',
      6: 'Tax Invoice Jobify',
      7: 'vKirirom Pte Invoice',
      8: 'Commercial Invoice package 2020',
      9: 'Tax Invoice package 2020',
      10: 'A2A Commercial Invoice',
      11: 'A2A Tax Invoice',
      12: 'KIT Commercial Invoice',
      13: 'KIT Tax Invoice',
      14: 'VKIS Invoice',
    }

    company_template = {
      'A2A Consolidate': [],
      'A2A Development Co.,Ltd': [10, 11],
      'A2A Town (Cambodia) Co., Ltd.': [],
      'Coin Cloud Co., Ltd': [],
      'Jobify (Cambodia) Co,.Ltd': [5, 6],
      'KIT Management Co., Ltd': [],
      'Kirirom Digital (Cambodia) Co,.Ltd': [3, 4],
      'Quadusk Pte.,Ltd': [],
      'vKirirom Japan Inc.': [],
      'vKirirom Pte.': [],
    }
    user_company = self.env.company.name
    if res.get('toolbar', False) and res.get('toolbar').get('print', False):
      print_button = [report_names[i] for i in company_template[user_company]]
      res['toolbar']['print'] = [report for report in res['toolbar']['print'] if report['name'] in print_button]

    # print(self)
    # from pprint import pprint
    # pprint(res)
    return res


