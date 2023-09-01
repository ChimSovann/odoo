from odoo import models
import math


class PosDiscount(models.AbstractModel):
  _inherit = 'pos.session'
  _description = "Create Discount line and adjust journal Item according to A2A requirement"

  def _create_account_move(self):
    super(PosDiscount, self)._create_account_move()
    journal_account = {}
    discount_account = {}

    def round_half_up(n, decimals=0):
      multiplier = 10 ** decimals
      return math.floor(n * multiplier + 0.5) / multiplier

    # Loop through each order and recalculate income account, tax account and discount account
    for order in self.order_ids:
      for order_line in order.lines:
        product_price = order_line.qty * order_line.price_unit
        product_account = str(order_line.product_id.categ_id.property_account_income_categ_id.id)
        if order_line.product_id.property_account_income_id:
          product_account = str(order_line.product_id.property_account_income_id.id)
        discount_account_id = order_line.product_id.categ_id.customer_discount_account_categ_id.id
        income_amount = product_price
        tax_amount = 0
        discount_amount = product_price * order_line.discount / 100
        income_name = 'Sales untaxed'

        if order_line.tax_ids:
          tax_account = ''
          for tax in order_line.tax_ids.invoice_repartition_line_ids:
            if tax.repartition_type == 'tax':
              tax_account = str(tax.account_id.id) + order_line.tax_ids.name
              income_name = 'Sales with ' + order_line.tax_ids.name
              tax_amount = round_half_up(product_price * order_line.tax_ids.amount / 100, 2)
              discount_amount = (income_amount + tax_amount) * order_line.discount / 100

              if order_line.tax_ids.price_include:
                income_amount = product_price / 1.1
                tax_amount = product_price - income_amount
                discount_amount = product_price * order_line.discount / 100

            journal_account[tax_account] = journal_account.get(tax_account, 0) + tax_amount

        journal_account[product_account + income_name] = journal_account.get(product_account + income_name,
                                                                             0) + income_amount
        discount_account[discount_account_id] = discount_account.get(discount_account_id, 0) + discount_amount

    if discount_account:
      debit_side = 0
      credit_side = 0

      # Update value of each account
      for line in self.move_id.line_ids:
        if line.account_internal_type == 'receivable':
          debit_side += line.debit
          continue
        line.with_context(check_move_validity=False).update(
          {'credit': round_half_up(journal_account[str(line.account_id.id) + line.name], 2)}
        )
        credit_side += line.credit

      # Create discount line
      for account, debit in discount_account.items():
        account_id = self.env['account.account'].search([('id', '=', account)])
        if debit != 0:
          if str(debit)[::-1].find('.') == 3 and str(debit)[-1] == '5':
            debit = float(str(debit)[:-1])
          else:
            debit = round(debit, 2)
          debit_side += round_half_up(debit, 2)
          self.move_id.line_ids.with_context(check_move_validity=False).create({
            'credit': 0.0,
            'debit': round_half_up(debit, 2),
            'name': "Discount Account",
            'account_id': account,
            'exclude_from_invoice_tab': True,
            'account_internal_type': account_id.user_type_id.type,
            'account_root_id': account_id.root_id.id,
            'move_id': self.move_id.id,
          })

      if credit_side != debit_side:
        for line in self.move_id.line_ids:
          if line.name == "VAT 10.00%":
            line.with_context(check_move_validity=False).update(
              {'credit': line.credit + debit_side - credit_side}
            )

      self.move_id._check_balanced()
