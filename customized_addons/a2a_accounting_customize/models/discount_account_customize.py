from odoo import models, fields, api, _
from odoo.exceptions import UserError
import math


class DiscountAccountMoveLine(models.Model):
  _inherit = 'account.move.line'

  discount_customize = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
  subtotal_customize = fields.Monetary(string='Subtotal', store=True, readonly=True, compute='compute_amount_customize')

  def round_half_up(self, n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier + 0.5) / multiplier

  @api.depends('quantity', 'price_unit', 'discount_customize', 'price_subtotal', 'tax_ids')
  def compute_amount_customize(self):
    for acc in self:
      for line in acc:
        line.subtotal_customize = self.round_half_up(
          line.quantity * line.price_unit * (1 - line.discount_customize / 100), 2)
        if line.tax_ids.price_include:
          line.subtotal_customize = self.round_half_up(line.quantity * line.price_unit / (1 + line.tax_ids.amount / 100) \
                                                       * (1 - line.discount_customize / 100), 2)


class DiscountAccountMove(models.Model):
  _inherit = 'account.move'

  amount_untaxed_customize = fields.Monetary(string='Untaxed Amount', store=True, readonly=True,
                                             compute="_compute_amount_customize")
  tax_amount_customize = fields.Monetary(string='Tax', store=True, readonly=True, compute="_compute_amount_customize")
  total_customize = fields.Monetary(string='Total', store=True, readonly=True, compute="_compute_amount_customize")

  def _compute_amount(self):
    super(DiscountAccountMove, self)._compute_amount()
    for move in self:
      type = move.type
      if type not in ['in_invoice', 'in_refund', 'in_receipt']:
        total = 0
        for line in move.line_ids:
          if move.is_invoice(include_receipts=True):
            # === Invoices ===
            if line.name == 'Discount Account':
              total += line.balance
        move.amount_total_signed -= total

  @api.depends('invoice_line_ids', 'line_ids')
  def _compute_amount_customize(self):
    company_currency_id = (self.company_id or self.env.company).currency_id
    for acc in self:
      type = acc.type
      if type not in ['in_invoice', 'in_refund', 'in_receipt']:
        amount_untax = 0
        receivable = 0
        for move in acc:
          for line in move.invoice_line_ids:
            amount_untax += line.subtotal_customize
          for line in move.line_ids:
            if line.account_internal_type == 'receivable':
              if acc.type == 'out_refund':
                receivable = line.credit
              else:
                receivable = line.debit
          move.total_customize = company_currency_id.round(receivable)
          move.amount_untaxed_customize = company_currency_id.round(amount_untax)
          move.tax_amount_customize = company_currency_id.round(move.total_customize - move.amount_untaxed_customize)

  def create(self, vals_list):
    # Case create invoice from other module:
    # set discount_customize = discount, and reset discount to zero
    if 'invoice_line_ids' in vals_list:
      for line in vals_list['invoice_line_ids']:
        line = line[2]
        if 'discount' in line:
          if line['discount']:
            line['discount_customize'] = line['discount']
            line['discount'] = 0
    res = super(DiscountAccountMove, self).create(vals_list)
    if 'line_ids' not in vals_list:
      res._create_dynamic_discount_lines()
    return res

  @api.onchange('invoice_line_ids')
  def _onchange_invoice_line_ids(self):
    # Set constraint if user didn't configure account into product's category and try to add discount
    if self.type not in ['in_invoice', 'in_refund', 'in_receipt']:
      for line in self.invoice_line_ids:
        if line.discount_customize:
          category_id = line.product_id.product_tmpl_id.categ_id
          discount_account_id = category_id.customer_discount_account_categ_id.id
          if not discount_account_id:
            raise UserError(_('Please define customer discount account for this product [%s]') % line.product_id.name)
    super(DiscountAccountMove, self)._onchange_invoice_line_ids()

  def _onchange_recompute_dynamic_lines(self):
    super(DiscountAccountMove, self)._onchange_recompute_dynamic_lines()
    if self.type not in ['in_invoice', 'in_refund', 'in_receipt']:
      self._create_dynamic_discount_lines()

  def _create_dynamic_discount_lines(self):
    company_currency_id = (self.company_id or self.env.company).currency_id
    in_draft_mode = self != self._origin
    out_refund_mode = self.type == 'out_refund'
    create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
      'account.move.line'].with_context(check_move_validity=False).create
    amount_to_deduct = 0
    discount_account = {}

    # Clear all discount line from journal items
    discount_lines = self.line_ids.filtered(lambda line: line.name == 'Discount Account')
    amount_to_deduct -= sum([line.debit if not out_refund_mode else line.credit for line in discount_lines])
    self.line_ids -= discount_lines

    # remove all journal items if there is no product in invoice line
    if not self.invoice_line_ids:
      self.line_ids = self.invoice_line_ids

    for line in self.invoice_line_ids:
      discount = line.discount_customize
      price = line.quantity * line.price_unit

      # Calculate discount amount for each discount account base on tax (include, exclude)
      if discount:
        category_id = line.product_id.product_tmpl_id.categ_id
        discount_account_id = category_id.customer_discount_account_categ_id.id
        tax_include = line.tax_ids.price_include
        tax_rate = line.tax_ids.amount
        if tax_include:
          discount_account[discount_account_id] = discount_account.get(discount_account_id,
                                                                       0) + price * discount / 100
        else:
          discount_account[discount_account_id] = discount_account.get(discount_account_id, 0) \
                                                  + (price - line.subtotal_customize) + \
                                                  (price * (tax_rate / 100) * (
                                                          line.discount_customize / 100))

    # Create discount line in journal items
    for id, amount in discount_account.items():
      if str(amount)[::-1].find('.') == 3 and str(amount)[-1] == '5':
        amount = float(str(amount)[:-1])
      else:
        amount = company_currency_id.round(amount)
      amount_to_deduct += amount
      account_id = self.env['account.account'].search([('id', '=', id)])
      credit = amount if out_refund_mode else 0.0
      debit = 0.0 if out_refund_mode else amount
      create_method({
        'credit': credit,
        'debit': debit,
        'name': "Discount Account",
        'account_id': id,
        'exclude_from_invoice_tab': True,
        'account_internal_type': account_id.user_type_id.type,
        'account_root_id': account_id.root_id.id,
        'move_id': self.id,
      })

    # Recalculate Account receivable after adding discount line
    for line in self.line_ids:
      if line.account_internal_type == 'receivable':
        if out_refund_mode:
          line.credit -= amount_to_deduct
        else:
          line.debit -= amount_to_deduct
        break

    # Remove discount line from invoice tab
    if in_draft_mode:
      self.invoice_line_ids = self.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)
