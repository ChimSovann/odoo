from odoo import models, fields, api
import datetime


class MarketListGeneralRequest(models.Model):
    _name = "market.list.general.request"
    _description = "Market List General Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # functions for default attributes
    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    def _get_default_currency(self):
        currency = self.env['res.currency'].search([('name', '=', 'USD')])
        return currency.id

    # Global fields
    name = fields.Char('Request Reference',
                       size=32,
                       tracking=True,
                       index=True,
                       readonly=True)

    requested_by = fields.Many2one('res.users',
                                   'Requester',
                                   required=True,
                                   tracking=True,
                                   readonly=True,
                                   default=_get_default_requested_by)

    creation_date = fields.Datetime('Creation date',
                                    help="Date when the user initiated the request.",
                                    readonly=True)

    approve_by = fields.Many2one('res.users',
                                 'Approver',
                                 tracking=True,
                                 required=True,
                                 domain=[('groups_id.name', '=', 'Request Manager')]
                                 )

    approve_date = fields.Datetime('Approved Date', readonly=True)

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          tracking=True,
                                          required=True,
                                          states={'approved': [('readonly', True)],
                                                  'done': [('readonly', True)]}
                                          )

    purchaser = fields.Many2one('res.users',
                                'Purchaser',
                                required=True,
                                domain=[('groups_id.name', '=', 'Purchaser')])

    description = fields.Text('Description')

    currency_id = fields.Many2one('res.currency',
                                  "Currency",
                                  default=_get_default_currency,
                                  domain=[('name', 'in', ('USD', 'KHR'))],
                                  )

    product_line_ids = fields.One2many('market.list.request.general.line',
                                       'request_id',
                                       'Products',
                                       readonly=False,
                                       states={'approved': [('readonly', True)],
                                               'done': [('readonly', True)]},
                                       copy=True
                                       )
    amount_total_est = fields.Float(string='Estimated Total Price',
                                    readonly=True,
                                    compute='_compute_amount_total_est'
                                    )

    # for tracking the status of purchase document
    _state_types = [
        ('draft', 'Draft'),
        ('to_approve', 'To be approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('done', 'Done')
    ]

    state = fields.Selection(selection=_state_types,
                             string='Status',
                             tracking=True,
                             required=True,
                             default='draft')

    # Global function
    def get_currency_id(self,
                        currency_name):
        """
            This function is use to find the ID of the currency in odoo.
            For example, you want to find the ID of the KHR currency in odoo.

            Args:
                -> Currency_name (String): name of the currency you want to find the ID of

            Return: the ID of the currency
        """
        currency = self.env['res.currency'].search([('name', '=', currency_name)])
        return currency.id

    # super functions section
    @api.model
    def create(self,
               vals_list):
        # converting vals_list into object just to make sure because
        # in the odoo document they mentioned that it could be type dict or list
        vals_list = dict(vals_list or {})
        # updating name field to a unique sequence for this record
        vals_list['name'] = self.env['ir.sequence'].next_by_code('general.request.sequence')
        # setting the creation date for the request
        vals_list['creation_date'] = datetime.datetime.today()
        # I use "[vals_list]" instead of just "vals_list" because the create function take list as an argument
        record = super(MarketListGeneralRequest, self).create([vals_list])
        assigned_to_partner_id = self.env['res.users'].browse(vals_list.get('approve_by')).partner_id.id
        if assigned_to_partner_id:
            # calling message_subscribe function to add user that has been selected as approve_by to record follower
            record.message_subscribe([assigned_to_partner_id])
        return record

    # if you're wondering why calling message_subscribe method in Creat and Write are different
    # for some reasons, in the Create method, you cant access fields value and parent methods thru self and it has be
    # called using Record
    # and for the Write method, you can access the fields value and parent methods thru self.

    def write(self,
              vals):
        record = super(MarketListGeneralRequest, self).write(vals)
        # I called this functions at the top because I need to access new updated value
        # meaning the self value after this line is an update it one
        # if you use self before this above line of you code you will get the before updated value

        assigned_to_partner_id = self.approve_by.partner_id.id
        requested_by_partner_id = self.requested_by.partner_id.id
        purchaser_partner_id = self.purchaser.partner_id.id

        # TODO: check to see what are the order of things that goes into both of these below
        # vals['message_follower_ids'] = [(6, 0, [assigned_to.partner_id.id, self.requested_by.partner_id.id])]
        # vals['message_follower_ids'] = [(4, self.purchaser.partner_id.id)]

        # this use to add assigned_to and requested_by user to the follower list
        # in case the approve_by field and the requested by has been changed
        self.message_subscribe([assigned_to_partner_id, requested_by_partner_id])

        if self.state == 'approved':
            # adding purchaser user to the record follower list after the request has been approved
            self.message_subscribe([purchaser_partner_id])
        return record

    def copy(self,
             default=None):
        default = dict(default or {})
        default.update({
            'creation_date': datetime.datetime.today(),
            'requested_by': self.env.uid,
        })
        return super(MarketListGeneralRequest, self).copy(default)

    # buttons functions
    def button_draft(self):
        self.state = 'draft'
        return True

    def button_to_approve(self):
        self.state = 'to_approve'
        return True

    def button_approved(self):
        self.state = 'approved'
        self.approve_date = datetime.datetime.today()
        self.approve_by = self.env.uid
        return True

    def button_rejected(self):
        self.state = 'rejected'
        return True

    def button_generate_po(self):
        self.state = 'done'
        order_line = []
        analytic_account_id = self.analytic_account_id.id
        date_order = datetime.datetime.today()

        for line in self.product_line_ids:
            order_line.append(
                [
                    0,
                    False,
                    {
                        'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'product_uom_id': line.product_uom_id.id,
                        'analytic_acc': analytic_account_id,
                        'date_order': date_order,
                        'supplier_id': line.supplier_id.id,
                        'currency_id': line.currency_id.id,
                        'price_per_unit': line.price_per_unit_est
                    }
                ]
            )

        vals_list = {
            'order_line': order_line,
            'origin': self.name,
            'analytic_account_id': analytic_account_id,
            'date_order': date_order,
            'request_date': self.creation_date,
            'is_a2a': False,
            'requested_by': self.requested_by.id,
            'approved_by': self.approve_by.id,
            'approved_date': self.approve_date
        }

        return self.env['kr.purchase.order'].create([vals_list])

    # computed method
    @api.onchange('product_line_ids')
    def _compute_amount_total_est(self):
        """
            this function use to sum up all the price of each product that has been
            selected inside the tree line view. Use inside compute field for price
            estimate for each tree line.

            Args:
                -> line_field : reference of the field name of the line field that has to be computed

            Return: the total sum of the estimate price
        """
        subtotal_khr = 0
        subtotal_usd = 0
        for line in self.product_line_ids:
            if line.currency_id.id == self.get_currency_id('USD'):
                subtotal_usd += line.total_price_est
            else:
                subtotal_khr += line.total_price_est

        self.amount_total_est = subtotal_usd + subtotal_khr / 4000
