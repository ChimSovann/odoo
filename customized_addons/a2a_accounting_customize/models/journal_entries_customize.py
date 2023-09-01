from odoo import models, api, fields


class JournalEntry(models.Model):
  _inherit = "account.move"

  old_number = fields.Char(string='Old Number')


class TrackingFields(models.AbstractModel):
  _inherit = "account.move"
  # Add tracking to all fields

  name = fields.Char(string='Number', required=True, readonly=True, copy=False, default='/',
                     track_visibility="onchange")
  date = fields.Date(string='Date', required=True, index=True, readonly=True,
                     states={'draft': [('readonly', False)]},
                     default=fields.Date.context_today, track_visibility="onchange")
  ref = fields.Char(string='Reference', copy=False, track_visibility="onchange")

  @api.model
  def _get_default_journal(self):
    return super(TrackingFields, self)._get_default_journal()

  journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                               states={'draft': [('readonly', False)]},
                               domain="[('company_id', '=', company_id)]",
                               default=_get_default_journal, track_visibility="onchange")
  company_id = fields.Many2one(comodel_name='res.company', string='Company',
                               store=True, readonly=True,
                               compute='_compute_company_id', track_visibility="onchange")
  line_ids = fields.One2many('account.move.line', 'move_id', string='Journal Items', copy=True, readonly=True,
                             states={'draft': [('readonly', False)]}, track_visibility="onchange")

  journal_tab_item = ['account_id', 'partner_id', 'name', 'analytic_account_id', 'debit', 'credit']

  auto_post = fields.Boolean(string='Post Automatically', default=False,
                             help='If this checkbox is ticked, this entry will be automatically posted at its date.',
                             track_visibility="onchange")
  reversed_entry_id = fields.Many2one('account.move', string="Reversal of", readonly=True, copy=False,
                                      track_visibility="onchange")
  to_check = fields.Boolean(string='To Check', default=False,
                            help='If this checkbox is ticked, it means that the user was not sure of all the related informations at the time of the creation of the move and that the move needs to be checked again.',
                            track_visibility="onchange")

  # Log msg if line is deleted
  def write(self, vals):
    if 'line_ids' in vals:
      line_id = vals['line_ids']
      for line in line_id:
        if line[0] == 2:
          msg = "<b>" + "Line id " + str(line[1]) + " has been deleted." + "</b><ul>"
          move_line = self.env['account.move.line'].search([('id', '=', line[1])])
          if move_line.account_id.name:
            msg += "<li>" + "Account: " + move_line.account_id.name + "</li>"
          if move_line.partner_id.name:
            msg += "<li>" + "Partner: " + move_line.partner_id.name + "</li>"
          if move_line.name:
            msg += "<li> Label: " + move_line.name + "</li>"
          if move_line.analytic_account_id:
            msg += "<li> Analytic account: " + move_line.analytic_account_id.name + "</li>"
          if move_line.debit:
            msg += "<li> Debit: " + str(move_line.debit) + "</li>"
          if move_line.credit:
            msg += "<li> Credit: " + str(move_line.credit) + "</li>"
          msg += "</ul>"
          self.message_post(body=msg)

    result = super(TrackingFields, self).write(vals)
    return result

  def _compute_amount(self):
    payment_state = {}
    for move in self:
      payment_state[move] = move.invoice_payment_state
    res = super(TrackingFields, self)._compute_amount()
    for move in self:
      if move.invoice_payment_state == 'paid' and move.invoice_payment_state != payment_state[move]:
        move.message_post(body='Invoice paid')

    return res


class GeneratePartnerLabelAccount(models.Model):
  _inherit = "account.move.line"

  # Auto generate Partner, account and label in line_ids

  @api.model
  def default_get(self, default_fields):
    # OVERRIDE
    values = super(GeneratePartnerLabelAccount, self).default_get(default_fields)

    if self._context.get('line_ids') and any(
            field_name in default_fields for field_name in ('debit', 'credit', 'account_id', 'partner_id')):
      move = self.env['account.move'].new({'line_ids': self._context['line_ids']})

      # Suggest default value for 'partner_id'.
      if 'partner_id' in default_fields and not values.get('partner_id'):
        if len(move.line_ids[-1:]) == 1:
          values['partner_id'] = move.line_ids[-1:].mapped('partner_id').id

      # Suggest default value for 'account_id'.
      if 'account_id' in default_fields and not values.get('account_id'):
        if len(move.line_ids[-1:]) == 1:
          values['account_id'] = move.line_ids[-1:].mapped('account_id').id

      # Suggest default value for 'label'.
      if 'name' in default_fields and not values.get('name'):
        if len(move.line_ids[-1:]) == 1:
          values['name'] = move.line_ids[-1:].mapped('name')[0]

    return values

  def _get_id(self):
    return self.id

  # Custom field to show id of each line
  id = fields.Char(string='id', default=_get_id, readonly=True)


class TrackLineFields(models.AbstractModel):
  _inherit = 'account.move.line'
  # Add tracking to fields in line_ids

  # Fields to track
  journal_tab_item = ['account_id', 'partner_id', 'name', 'analytic_account_id', 'debit', 'credit']

  cycle = 0
  count = 0

  def _update_line(self, values):
    for key in values:
      if key in self.journal_tab_item:
        self.count += 1
        self.cycle += 1
    lines = self.mapped('move_id')
    for line in lines:
      move_lines = self.filtered(lambda x: x.move_id == line)
      msg = "<b>" + "Line id " + str(self.id) + " has been updated." + "</b><ul>"
      for item in values:
        if item != 'tax_exigible' and item in self.journal_tab_item:
          for l in move_lines:
            try:
              prev = getattr(l, item)
              new = values[item]

              if item == 'account_id':
                prev = l.account_id.name
                new = self.env['account.account'].search([('id', '=', new)], limit=1).name
                item = 'Account'
              elif item == 'analytic_account_id':
                prev = l.analytic_account_id.name
                new = self.env['account.analytic.account'].search([('id', '=', new)], limit=1).name
                item = 'Analytic Account'
              elif item == 'name':
                item = 'Label'
              elif item == 'partner_id':
                prev = l.partner_id.name
                new = self.env['res.partner'].search([('id', '=', new)], limit=1).name
                item = 'Partner'
              if item in ['debit', 'credit']:
                prev = round(prev, 2)
                new = round(new, 2)
              if prev != new:
                msg += "<li>" + item + ": %s -> %s" % (
                  prev, new,) + "</li>"

            except:
              pass

      msg += "</ul>"
      if self.count == 1 or self.count == self.cycle - self.cycle ** (1 / 2) + 1:
        if msg != "<b>" + "Line id " + str(self.id) + " has been updated." + "</b><ul></ul>":
          line.message_post(body=msg)
        self.cycle = 0
        self.count = 0
      self.count -= 1

  def write(self, values):
    for item in self.journal_tab_item:
      if item in values:
        self._update_line(values)

    result = super(TrackLineFields, self).write(values)
    return result

  def create(self, vals_list):
    result = super(TrackLineFields, self).create(vals_list)
    list_id = [str(line.id) for line in result]
    if len(list_id) == 1:
      vals_list = [vals_list]
    index = 0
    lines = result.mapped('move_id')
    for line in lines:
      for line_id in vals_list:
        msg = "<b>" + "Line id " + list_id[index] + " has been created." + "</b><ul>"
        for key in line_id:
          if key in self.journal_tab_item:
            if line_id[key]:
              item = key
              value = line_id[key]
              if key == 'account_id':
                value = self.env['account.account'].search([('id', '=', value)], limit=1).name
                item = 'Account'
              elif key == 'analytic_account_id':
                value = self.env['account.analytic.account'].search([('id', '=', value)], limit=1).name
                item = 'Analytic Account'
              elif key == 'name':
                item = 'Label'
              elif key == 'partner_id':
                value = self.env['res.partner'].search([('id', '=', value)], limit=1).name
                item = 'Partner'
              msg += "<li>" + item + ": " + str(value) + "</li>"
        msg += "</ul>"
        line.message_post(body=msg)
        index += 1

    return result
