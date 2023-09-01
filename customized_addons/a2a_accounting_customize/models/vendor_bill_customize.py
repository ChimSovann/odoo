from odoo import models, api, fields


class VendorBillCustomize(models.Model):
  _inherit = 'account.move'
  vendor_bill_no = fields.Char(string="Vendor Bill Number", readonly=True, states={'draft': [('readonly', False)]}, )
  account = property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                          string="Account Payable",
                                                          related="partner_id.property_account_payable_id",
                                                          tracking=True
                                                          )
  invoice_origin = fields.Char(string='Origin', readonly=True, tracking=True, states={'draft': [('readonly', False)]},
                               help="The document(s) that generated the invoice.")

  purchaser = fields.Many2one('res.users', copy=False, tracking=True, string='Purchaser',
                              domain=[('groups_id.category_id.name', '=', 'Purchase')])

  def write(self, vals):
    for move in self:
      if move.name != '/' and 'journal_id' in vals and move.journal_id.id != vals['journal_id']:
        move.name = '/'
    return super(VendorBillCustomize, self).write(vals)

  posted_name = fields.Char('Posted Number', required=False, readonly=True, copy=False, default='/')

  def post(self):
    for move in self:
      if not move.name.startswith(move.journal_id.code) and move.name != '/':
        move.name = '/'
      if move.posted_name.startswith(move.journal_id.code):
        move.name = move.posted_name
    return super().post()


class RegisterPayment(models.Model):
  _inherit = 'account.payment'

  def post(self):
    return_val = super().post()
    for rec in self:
      if rec.payment_difference_handling == 'reconcile':
        journal_item = self.env['account.move.line'].search([('payment_id', '=', rec.id),
                                                             ('name', '=', rec.writeoff_label)])
        payment_diff = journal_item.credit - journal_item.debit
        self.env['account.analytic.line'].create(
          [{
            'name': journal_item.name,
            'partner_id': journal_item.partner_id.id,
            'date': journal_item.move_id.date,
            'move_id': journal_item.id,
            'unit_amount': journal_item.quantity,
            'general_account_id': journal_item.account_id.id,
            'amount': payment_diff,
            'account_id': rec.analytic_id.id,
            'ref': rec.payment_ref,
            'company_id': rec.company_id.id,
          }]
        )
    return return_val
