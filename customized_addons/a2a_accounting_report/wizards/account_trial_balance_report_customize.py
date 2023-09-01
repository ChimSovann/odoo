from collections import defaultdict, deque

from odoo import models


class TrialBalance(models.AbstractModel):
  _inherit = ['report.accounting_pdf_reports.report_trialbalance']

  def _process_parent(self, account_entry_tree, level):
    account_entry_hierarchy = defaultdict(list)

    for key, values in account_entry_tree.items():
      account = self.env['account.account'].with_context(
        company_id=self.env.context.get("company_id")).browse(key)
      account_entry_hierarchy[account.parent_id.id].append({key: values})

    for key, values in account_entry_hierarchy.copy().items():
      parent_account = self.env['account.account'].with_context(
        company_id=self.env.context.get("company_id")).browse(key)
      debit = sum([list(i.values())[0][1][0] for i in values])
      credit = sum([list(i.values())[0][1][1] for i in values])
      balance = sum([list(i.values())[0][1][2] for i in values])
      code = parent_account.code

      account_entry_hierarchy.pop(key, None)
      account_entry_hierarchy[key] = [values, [debit, credit, balance], level - 1, code]
    return account_entry_hierarchy

  @staticmethod
  def _preorder_traversal_account_entry(root):
    stack = deque([])
    preorder = list()
    if not root:  # handle case: no account entry
      return preorder
    preorder.append([list(root.keys())[0], list(root.values())[0][1], list(root.values())[0][2]])
    stack.append(root)
    while len(stack) > 0:
      flag = 0
      if len(list(stack[len(stack) - 1].values())[0][0]) == 0:
        x = stack.pop()

      else:
        par = stack[len(stack) - 1]

        for i in range(0, len(list(par.values())[0][0])):
          if [list(list(par.values())[0][0][i].keys())[0],
              list(list(par.values())[0][0][i].values())[0][1],
              list(list(par.values())[0][0][i].values())[0][2]] \
                  not in preorder:
            flag = 1
            stack.append(list(par.values())[0][0][i])
            preorder.append(
              [list(list(par.values())[0][0][i].keys())[0],
               list(list(par.values())[0][0][i].values())[0][1],
               list(list(par.values())[0][0][i].values())[0][2]])
            break

        if flag == 0:
          stack.pop()

    return preorder

  def _get_accounts(self, accounts, display_account):
    """ compute the balance, debit and credit for the provided accounts
        :Arguments:
            `accounts`: list of accounts record,
            `display_account`: it's used to display either all accounts or those accounts which balance is > 0
        :Returns a list of dictionary of Accounts with following key and value
            `name`: Account name,
            `code`: Account code,
            `credit`: total amount of credit,
            `debit`: total amount of debit,
            `balance`: total amount of balance,
    """

    account_result = {}
    # Prepare sql query base on selected parameters from wizard
    tables, where_clause, where_params = self.env['account.move.line']._query_get()
    tables = tables.replace('"', '')
    if not tables:
      tables = 'account_move_line'
    wheres = [""]
    if where_clause.strip():
      wheres.append(where_clause.strip())
    filters = " AND ".join(wheres)
    # compute the balance, debit and credit for the provided accounts
    request = (
              "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
              " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
    params = (tuple(accounts.ids),) + tuple(where_params)
    self.env.cr.execute(request, params)
    for row in self.env.cr.dictfetchall():
      account_result[row.pop('id')] = row

    account_res = []
    max_level = 0
    account_entry_tree = dict()
    for account in accounts:
      is_append = False
      res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
      currency = account.currency_id and account.currency_id or account.company_id.currency_id
      res['code'] = account.code
      res['name'] = account.name
      if account.id in account_result:
        res['debit'] = account_result[account.id].get('debit')
        res['credit'] = account_result[account.id].get('credit')
        res['balance'] = account_result[account.id].get('balance')
      if display_account == 'all':
        is_append = True
      if display_account == 'not_zero' and not currency.is_zero(res['balance']):
        is_append = True
      if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
        is_append = True

      level = 0
      parent_account = account.parent_id
      if is_append:
        while parent_account:
          parent_account = parent_account.parent_id
          level += 1
        account_entry_tree[account.id] = [[], [res['debit'], res['credit'], res['balance']], level, res['code']]
      max_level = max(max_level, level)

    account_entry_tree_res = {}
    while max_level > 0:
      for key, value in account_entry_tree.copy().items():
        if value[2] == max_level:
          account_entry_tree.pop(key, None)
          if key not in account_entry_tree_res:
            account_entry_tree_res.update({key: value})

      sorted_account_entry_tree_res = dict(sorted(account_entry_tree_res.items(), key=lambda x: x[1][3]))
      process_parent_result = self._process_parent(sorted_account_entry_tree_res, max_level)
      account_entry_tree_res = process_parent_result
      max_level -= 1

    account_entry_list = self._preorder_traversal_account_entry(account_entry_tree_res)

    for i in range(0, len(account_entry_list)):
      account = self.env['account.account'].with_context(company_id=self.env.context.get("company_id")).browse(
        account_entry_list[i][0])
      res = {
        'code': account.code,
        'name': account.name,
        'is_parent': account.is_parent,
        'type': account.user_type_id.name,
        'level': account_entry_list[i][2],
        'debit': account_entry_list[i][1][0],
        'credit': account_entry_list[i][1][1],
        'balance': account_entry_list[i][1][2]
      }

      account_res.append(res)

    return account_res
