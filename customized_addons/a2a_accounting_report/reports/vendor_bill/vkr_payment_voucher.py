from odoo import models
import json


class VkrPaymentVoucher(models.AbstractModel):
  _inherit = "account.move"

###################################################################
# - inherit data from account.move                                #
# - write a function to get data through payment widget           #
# - getting data from aacount.move.line, account.payment          #
# - write function to calculate and get data for debit, credits   #
#   for account payable row                                       #
###################################################################

# for payment widget
  def get_vendor_bill_data(self, payments_widget):
    if payments_widget == 'false':
      return
    content = json.loads(payments_widget)
    payment_object = dict()
    for item in content['content']:
      # Getting payment bill data
      payment_table = self.env['account.move.line'].browse([item['payment_id'], item['payment_id']+1])
      payment_ref = self.env['account.move.line'].browse(item['payment_id']+1).name
      memo = self.env['account.payment'].search([('name', '=', payment_ref)]).communication

      date_reformat = item['date'][-2:] + "/" + item['date'][5:7] + "/" + item['date'][0:4]

      for data_payment in payment_table:
        if payment_ref not in payment_object:
          payment_object[payment_ref] = {
            'label': [data_payment.name],
            'journal': [item['journal_name']],
            'debit': [data_payment.debit],
            'credit': [data_payment.credit],
            'partner': [data_payment.partner_id.name],
            'account_code': [data_payment.account_id.code],
            'account_name': [data_payment.account_id.name],
            'date': date_reformat,
            'amount': [round(item['amount'], 2)],
            'remark': [item['ref']],
            'analytic_acc': [data_payment.analytic_account_id.name],
            'memo':[ memo],
          }
        else:
          payment_object[payment_ref]['label'].append(data_payment.name)
          payment_object[payment_ref]['journal'].append(item['journal_name'])
          payment_object[payment_ref]['debit'].append(data_payment.debit)
          payment_object[payment_ref]['credit'].append(data_payment.credit)
          payment_object[payment_ref]['partner'].append(data_payment.partner_id.name)
          payment_object[payment_ref]['account_code'].append(data_payment.account_id.code)
          payment_object[payment_ref]['account_name'].append(data_payment.account_id.name)
          payment_object[payment_ref]['amount'].append(round(item['amount'], 2))
          payment_object[payment_ref]['remark'].append(item['ref'])
          payment_object[payment_ref]['analytic_acc'].append(data_payment.analytic_account_id.name)
          payment_object[payment_ref]['memo'].append( memo)

    return payment_object
# to get total of debit and credit and account payable
  def get_total_of_payment_voucher(self):
    total_debit = 0
    for value in self.invoice_line_ids:
      total_debit += value.debit

    return total_debit

#for acc payable
  def _get_account_payable(self):
    total_credit = 0
    for line in self.line_ids:
      total_credit += line.credit
      if line.account_id.user_type_id.name == 'Accounts Payable':
        return line, total_credit
    return False, total_credit

