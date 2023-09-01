from odoo import fields, models


class CustomizeFinancialAccountLine(models.AbstractModel):
  _inherit = 'report.accounting_pdf_reports.report_financial'

  def get_account_lines(self, data):
    lines = super(CustomizeFinancialAccountLine, self).get_account_lines(data)
    added_parent = []
    sum_acc = {}
    prev = ''
    report = ''

    for index, line in enumerate(lines):
      # prevent duplicate iteration
      if line['name'] == prev:
        continue
      if line['type'] == 'report':
        report = line['name']
      # check to find leaf node
      if line['type'] == 'account':
        code = line['name'].split()[0]
        account = self.env['account.account'].search([('code', '=', code)]).parent_id
        company_id = data['company_id'][0]
        # In case get multiple account after search, filter and get the one with the selected company in wizard
        if len(account) > 1:
          for acc in account:
            if acc.company_id.id == company_id:
              account = acc
              continue
        sub_lines = []
        level = line['level']
        # loop to get all the parent of the same code hierarchy ex. 141000(leaf node)->...>100000(parent node)
        while account.parent_id.name:
          vals = {
            'name': account.code + ' ' + account.name,
            'balance': 0.0,
            'debit': 0.0,
            'credit': 0.0,
            'balance_cmp': 0.0,
            'type': 'account_parent',
            'level': 0,
            'account_type': account.internal_type,
          }

          # calculate the credit, debit and balance of parent
          if report + account.code in sum_acc:
            sum_acc[report + account.code]['balance'] += line['balance']
            if data['debit_credit']:
              sum_acc[report + account.code]['credit'] += line['credit']
              sum_acc[report + account.code]['debit'] += line['debit']
            if data['enable_filter']:
              sum_acc[report + account.code]['balance_cmp'] += line['balance_cmp']
          else:
            sum_acc[report + account.code] = {'balance': 0.0,
                                              'debit': 0.0,
                                              'credit': 0.0,
                                              'balance_cmp': 0.0}
            sum_acc[report + account.code]['balance'] = line['balance']
            if data['debit_credit']:
              sum_acc[report + account.code]['credit'] = line['credit']
              sum_acc[report + account.code]['debit'] = line['debit']
            if data['enable_filter']:
              sum_acc[report + account.code]['balance_cmp'] = line['balance_cmp']
          # calculate level for the child node
          if report + account.code in added_parent:
            level += 1
          # check if parent and child code is in the same hierarchy
          # and prevent duplicate parent on each leaf node
          if len(''.join(filter(str.isdigit, code))) == len(
                  ''.join(filter(str.isdigit, account.code))) and report + account.code not in added_parent:
            added_parent.append(report + account.code)
            sub_lines.insert(0, vals)
          account = account.parent_id
        # set level for both child and parent node
        for i, l in enumerate(sub_lines):
          l['level'] = level + i
          lines.insert(index, sub_lines[-1 * (i + 1)])
        level += len(sub_lines)
        line['level'] = level
        prev = line['name']
    # set credit, debit and balance for parent
    for line in lines:
      code = line['name'].split()[0]
      if line['type'] == 'report':
        report = line['name']
      if report + code in sum_acc:
        line['balance'] = sum_acc[report + code]['balance']
        line['credit'] = sum_acc[report + code]['credit']
        line['debit'] = sum_acc[report + code]['debit']
        line['balance_cmp'] = sum_acc[report + code]['balance_cmp']
    return lines
