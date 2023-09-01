from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv.osv import except_osv

_STATES = [
    ('draft', 'Draft'),
    ('progress', 'Progress'),
    ('validate', 'Validated'),
    ('done', 'Done'),
]


class MarketListPurchaseOrder(models.Model):
    _name = 'kr.purchase.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Order Reference", required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    origin = fields.Char('Origin', required=True)
    request_date = fields.Datetime('Requested Date')
    approved_date = fields.Datetime('Approved Date')
    date_order = fields.Date('Order Date', required=True)
    payment_date = fields.Datetime('Payment Date', tracking=True)
    requested_by = fields.Many2one(
        'res.users', 'Requested By', tracking=True)
    approved_by = fields.Many2one(
        'res.users', 'Approved By', tracking=True)
    validate_by = fields.Many2one(
        'res.users', 'Validate By', tracking=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account', tracking=True)
    picking = fields.Many2one(
        'stock.picking', 'Picking', tracking=True, readonly=True)
    entry_ref = fields.Many2one(
        'account.move', 'Entry Reference')
    budget_controller = fields.Many2one('res.users', 'Budget Controller',
                                        states={'done': [('readonly', True)]})
    is_a2a = fields.Boolean('Is A2AGR?')

    # These codes were commented because kr.purchase.order.line is not available right now
    order_line = fields.One2many('kr.purchase.order.line', 'order_id', 'Order Lines', copy=True, ondelete='cascade',
                                 required=True)
    # order_line_fk = fields.Many2one(
    #     "kr.purchase.order.line", string="Order Line", ondelete="cascade", required=True)
    amount_riel = fields.Float('Amount KHR (៛)', readonly='True', tracking=True,
                               compute='_compute_amount_riel')
    amount_usd = fields.Float('Amount USD ($)', readonly='True', tracking=True,
                              compute='_compute_amount_usd')
    exchange_rate = fields.Float('Exchange Rate', default=4000,
                                 tracking=True)
    amount_riel_usd = fields.Float('From KHR to USD', readonly='True', tracking=True,
                                   compute='_compute_amount_riel_usd')
    amount_total = fields.Float('Total Amount ($)', readonly='True', tracking=True,
                                compute='_compute_amount_total')
    state = fields.Selection(
        selection=_STATES, string="Status", readonly=True, default='draft')
    description = fields.Text('Description')
    journal_id = fields.Many2one('account.journal', 'Journal', required=False, tracking=True,
                                 states={'progress': [('required', True)],
                                         'validate': [('readonly', True)],
                                         'done': [('readonly', True)]},
                                 readonly=False)
    debit_acc = fields.Many2one('account.account', 'Debit Account', required=False, tracking=True,
                                states={'progress': [('required', True)],
                                        'validate': [('required', True)],
                                        'done': [('readonly', True)]},
                                readonly=False)
    credit_acc = fields.Many2one('account.account', 'Credit Account', required=False, tracking=True,
                                 states={'progress': [('required', True)],
                                         'validate': [('required', True)],
                                         'done': [('readonly', True)]},
                                 readonly=False)
    currency_id_khr = fields.Many2one('res.currency', "Currency KHR", default=66,
                                      domain=[('name', 'in', ['KHR'])])
    currency_id_usd = fields.Many2one(
        'res.currency', "Currency USD", default=2)
    receive_btn_tracker = fields.Char("Receive Button Tracker", compute="_compute_btn_tracker")

    # This function is used to track the product type in order line to
    # set condition for Receive Prodcut button visibility

    @api.depends('order_line')
    def _compute_btn_tracker(self):
        move_lines = []
        for line in self.order_line:
            if line.product_id.type == "product":
                move_lines.append(line)
        if len(move_lines) > 0:
            self.receive_btn_tracker = "HAS PRODUCT"
        else:
            self.receive_btn_tracker = "HAS NO PRODUCT"

    @api.constrains('debit_acc')
    def _set_debit_acc_line(self):
        for line in self.order_line:
            line.debit_acc = self.debit_acc.id

    # These codes were commented because kr.purchase.order.line is not available right now
    # This method is used to calculate the total amount of cost using KHR currency from each line
    @api.onchange("order_line")
    def _compute_amount_riel(self):
        tallies = 0
        for line in self.order_line:
            if line.currency_id.name == 'KHR':
                tallies += line.sub_total
        self.amount_riel = tallies

    # This method is used to calculate the total amount of cost using USD currency from each line
    @api.onchange("order_line")
    def _compute_amount_usd(self):
        tallies = 0
        for line in self.order_line:
            if line.currency_id.name == 'USD':
                tallies += line.sub_total
        self.amount_usd = tallies

    # This method is used to convert from KHR to USD
    @api.onchange("amount_riel", "exchange_rate")
    def _compute_amount_riel_usd(self):
        if self.exchange_rate != 0:
            self.amount_riel_usd = round(
                self.amount_riel / self.exchange_rate, 2)
        else:
            self.amount_riel_usd = round(self.amount_riel / 4000, 2)

    # This method is used to sum up the total amount from every product
    @api.onchange("amount_riel", "amount_usd", "exchange_rate")
    def _compute_amount_total(self):
        self.amount_total = self.amount_usd + self.amount_riel_usd

    # actions buttons for status bar interaction
    @api.model
    def create(self,
               vals_list):
        vals_list = dict(vals_list or {})
        if vals_list.get('name', _('New')) == _(('New')):
            if "A2AGR" in vals_list['origin']:
                vals_list['name'] = self.env['ir.sequence'].get(
                    'a2apo.sequence') or _('New')
            else:
                vals_list['name'] = self.env['ir.sequence'].next_by_code(
                    'vpo.sequence') or _('New')
        res = super(MarketListPurchaseOrder, self).create(vals_list)
        return res

    def write(self,
              vals_list):
        if 'state' in vals_list:
            # If the 'state' is in progress and validate_by field is not field
            # You cannot move on to the next state
            if vals_list['state'] == 'progress':
                if not self.validate_by:
                    raise except_osv(_('Warning'), _(
                        'Please input validate by!'))
                # raise warning when currency field is not filled
                # raise warning when invoice and supplier fields are not filled
                for line in self.order_line:
                    if not line.currency_id:
                        raise except_osv(_('Warning'), _(
                            'Please input all Currency ID (KHR/USD)'))
                    if not line.supplier_id or not line.invoice_number:
                        raise except_osv(_('Warning'), _(
                            'Please input all invoice number and supplier'))
            if vals_list['state'] == 'done':
                if self.description is False:
                    raise except_osv(_('Warning'), _(
                        'Please write down the description before clicking payment!'))
        return super(MarketListPurchaseOrder, self).write(vals_list)

    # This button will set the state to 'progress'
    # And also does what exactly what Receive Product button does
    def button_to_progress(self):
        if self.receive_btn_tracker == "HAS PRODUCT":
            self.button_receiver_product()
        self.state = 'progress'
        return True

    # This button will set the state to 'validate'
    def button_validate(self):
        self.state = 'validate'
        return True

    # This button will send the product(s) in the order line to the warehouse
    # and picking field will automatically generate the name of the warehouse after clicked the button
    def button_receiver_product(self):
        vk_location_id = self.env["stock.location"].search(
            [('complete_name', '=', 'VKWH/VKStock')])
        a2a_location_id = self.env["stock.location"].search(
            [('complete_name', '=', 'A2AWH/A2AStock')])
        a2a_operation_type = self.env["stock.picking.type"].search(['&', ('warehouse_id.code', '=', 'A2AWH'),
                                                                    ('company_id.partner_id.name', '=',
                                                                     'A2A Town (Cambodia) Co., Ltd.'),
                                                                    ('name', '=', 'Receipts')])
        vk_operation_type = self.env["stock.picking.type"].search(['&', ('warehouse_id.code', '=', 'VKWH'),
                                                                   ('company_id.partner_id.name', '=',
                                                                    'A2A Town (Cambodia) Co., Ltd.'),
                                                                   ('name', '=', 'Receipts')])
        source_location_id = self.env["stock.location"].search(
            [('complete_name', '=', 'Partner Locations/Vendors')])

        # Checking if the products are from VKGR, A2AGR, MKLR
        if 'VKGR' in self.origin or 'A2AGR' in self.origin or 'MKLR' in self.origin or 'PVKR' in self.origin:
            picking_obj = self.env['stock.picking']
            group_id = self.env["procurement.group"].create(
                {'name': self.name})
            move_lines = []
            # Loop through the order line
            for line in self.order_line:
                # Check if each product is the type 'product'
                # if it is append to move_lines list
                if line.product_id.type == 'product':
                    product_line = [0, False, {'product_id': line.product_id.id,
                                               'product_uom_qty': line.product_qty,
                                               'quantity_done': line.product_qty,
                                               'date': self.date_order,
                                               'date_expected': self.date_order,
                                               'state': 'assigned',
                                               'name': line.product_id.name,
                                               'product_uom': line.product_id.uom_id.id,
                                               'group_id': group_id.id
                                               }]
                    move_lines.append(product_line)
            # If there are products with type 'product' then
            # create vals_list
            if len(move_lines) > 0:
                vals_list = {
                    'origin': self.name,
                    'request_reference': self.origin,
                    'partner_id': False,
                    'date_done': self.date_order,
                    'move_type': 'direct',
                    'note': "",
                    'location_id': source_location_id.id,
                    'state': 'assigned',
                    'move_lines': move_lines,
                    'group_id': group_id.id,
                }
                # if the product is from VKGR, and MKLR, then update
                # vals_list to add the destination
                if 'MKLR' in self.origin or 'PVKR' in self.origin or 'VKGR' in self.origin:
                    vals_list.update(
                        {'picking_type_id': vk_operation_type.id, 'location_dest_id': vk_location_id.id})
                # if the product is from A2AGR then update
                # vals_list to add the destination
                elif 'A2AGR' in self.origin:
                    vals_list.update(
                        {'picking_type_id': a2a_operation_type.id, 'location_dest_id': a2a_location_id.id})
                # Create
                res = picking_obj.create(vals_list)
                self.picking = res

    # for calling account.move.action_post and get the entry name and post to the log
    def action_post(self,
                    invoice_id):
        self.entry_ref.action_post()
        account_move = self.env['account.move'].search(
            [('id', '=', invoice_id)])

        display_msg = """
                       <ul>
                            <li>
                                Entry Reference:
                                """ + str(account_move.name) + """
                            </li>
                        </ul>
                    """
        if self.id:
            self.message_post(body=display_msg)

    # This button will create 2 journal entries (debit and credit) in Journal items
    # then automatically generate the journal entry in entry_ref field
    def create_move(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']

        move_vals = {
            'name': '/',
            'date': self.payment_date,
            'ref': self.name,
            'journal_id': self.journal_id.id,
        }

        move_id = move_obj.create(move_vals)
        # Initialize 2 journal entries (debit and credit) values
        journal_debit = {
            'name': self.description,
            'ref': self.name,
            'move_id': move_id.id,
            'account_id': self.debit_acc.id,
            'debit': self.amount_total,
            'credit': 0.0,
            'journal_id': self.journal_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'date': self.payment_date,
        }
        journal_credit = {
            'name': self.description,
            'ref': self.name,
            'move_id': move_id.id,
            'account_id': self.credit_acc.id,
            'credit': self.amount_total,
            'debit': 0.0,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
        }
        # Create debit and credit account fields in account_move_line
        move_line_obj.create([journal_debit, journal_credit])
        # Change state to 'done' and generate journal entry name in entry_ref field
        self.write({'state': 'done', 'entry_ref': move_id.id})
        self.env.context = dict(self.env.context)
        self.env.context.update({'name': self._name})
        self.action_post(move_id.id)
        return True

    # Reset button for turning back the state to 'draft' state
    def button_to_draft(self):
        self.state = 'draft'
        return True
