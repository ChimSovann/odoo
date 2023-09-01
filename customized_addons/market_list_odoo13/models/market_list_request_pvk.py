from odoo import models, fields, api
import datetime


class MarketListPVKRequest(models.Model):
    _name = "market.list.pvk.request"
    _description = 'Market List PVK request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # functions for default attributes
    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    def _get_default_currency(self):
        currency = self.env['res.currency'].search([('name', '=', 'USD')])
        return currency.id

    # end of default functions

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

    amount_total_est = fields.Float(string='Estimated Total Price',
                                    readonly=True,
                                    compute='_compute_amount_total_est')

    # line ids
    veg_herb_line_ids = fields.One2many('market.list.pvk.request.vegetable.and.herb.line',
                                        'request_id',
                                        'Vegetable & Herb',
                                        readonly=False,
                                        states={'approved': [('readonly', True)],
                                                'done': [('readonly', True)]},
                                        copy=True
                                        )

    fruit_line_ids = fields.One2many('market.list.pvk.request.fruit.line', 'request_id',
                                     'Fruit',
                                     readonly=False,
                                     states={'approved': [('readonly', True)],
                                             'done': [('readonly', True)]},
                                     copy=True
                                     )

    poultry_line_ids = fields.One2many('market.list.pvk.request.poultry.line', 'request_id',
                                       'Poultry',
                                       readonly=False,
                                       states={'approved': [('readonly', True)],
                                               'done': [('readonly', True)]},
                                       copy=True
                                       )

    sea_fish_line_ids = fields.One2many('market.list.pvk.request.seafood.and.fish.line', 'request_id',
                                        'Seafood & Fish',
                                        readonly=False,
                                        states={'approved': [('readonly', True)],
                                                'done': [('readonly', True)]},
                                        copy=True
                                        )

    beef_pork_line_ids = fields.One2many('market.list.pvk.request.beef.and.pork.line', 'request_id',
                                         'Beef & Pork',
                                         readonly=False,
                                         states={'approved': [('readonly', True)],
                                                 'done': [('readonly', True)]},
                                         copy=True
                                         )

    other_line_ids = fields.One2many('market.list.pvk.request.other.line', 'request_id',
                                     'Other',
                                     readonly=False,
                                     states={'approved': [('readonly', True)],
                                             'done': [('readonly', True)]},
                                     copy=True
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

    def sum_total_price(self,
                        line_field
                        ):
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

        for line in line_field:
            if line.currency_id.id == self.get_currency_id('USD'):
                subtotal_usd += line.total_price_est
            else:
                subtotal_khr += line.total_price_est

        return subtotal_usd + subtotal_khr / 4000

    # super function section
    @api.model
    def create(self,
               vals_list):
        # converting vals_list into object just to make sure because
        # in the odoo document they mentioned that it could be type dict or list
        vals_list = dict(vals_list or {})
        # updating name field to a unique sequence for this record
        vals_list['name'] = self.env['ir.sequence'].next_by_code('pvk.request.sequence')
        # setting the creation date for the request
        vals_list['creation_date'] = datetime.datetime.today()
        # I use "[vals_list]" instead of just "vals_list" because the create function take list as an argument
        record = super(MarketListPVKRequest, self).create([vals_list])
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
        record = super(MarketListPVKRequest, self).write(vals)
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
        return super(MarketListPVKRequest, self).copy(default)

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
        # TODO: don't forget to uncomment here before push
        self.state = 'done'

        order_line = []
        analytic_account_id = self.analytic_account_id.id
        date_order = datetime.datetime.today()

        # lines
        veg_herb, fruit, poultry = [], [], []
        sea_fish, beef_pork, other = [], [], []

        #  length of each lines
        veg_herb_length = len(self.veg_herb_line_ids)
        fruit_length = len(self.fruit_line_ids)
        poultry_length = len(self.poultry_line_ids)
        sea_fish_length = len(self.sea_fish_line_ids)
        beef_pork_length = len(self.beef_pork_line_ids)
        other_length = len(self.other_line_ids)

        # find max length of the lines
        max_length = max([
            veg_herb_length,
            fruit_length,
            poultry_length,
            sea_fish_length,
            beef_pork_length,
            other_length,
        ])

        def add_item(iterate_index,
                     line_length,
                     line_list,
                     line_ids):
            """
                this function use for adding menu item that has been iterated thru
                to the its individual line_list that it is belong to

                Params:
                    -> iterate_index: it is a index value from the for loop
                    -> line_length: the variable that store the length of the menu line
                    -> line_list: the list to store item for each menu line
                    -> line_ids: the menu line_ids field
            """
            # checking to see if the index hasn't exceed the list range
            # before proceeding onward
            if iterate_index < line_length:
                product = line_ids[iterate_index]
                line_list.append([0, False, {
                    'product_id': product.product_id.id,
                    'product_qty': product.product_qty,
                    'product_uom_id': product.product_uom_id.id,
                    'analytic_acc': self.analytic_account_id.id,
                    'date_order': date_order,
                    # TODO: because supplier model is not connected yet, so it is commented for now
                    'supplier_id': product.supplier_id.id,
                    'currency_id': product.currency_id.id,
                    'price_per_unit': product.price_per_unit_est
                }])

        for index in range(0, max_length):
            add_item(index, veg_herb_length, veg_herb, self.veg_herb_line_ids)
            add_item(index, fruit_length, fruit, self.fruit_line_ids)
            add_item(index, poultry_length, poultry, self.poultry_line_ids)
            add_item(index, sea_fish_length, sea_fish, self.sea_fish_line_ids)
            add_item(index, beef_pork_length, beef_pork, self.beef_pork_line_ids)
            add_item(index, other_length, other, self.other_line_ids)

        order_line = veg_herb + fruit + poultry + sea_fish + beef_pork + other

        vals_list = {
            'order_line': order_line,
            'origin': self.name,
            'analytic_account_id': self.analytic_account_id.id,
            'date_order': date_order,
            'request_date': self.creation_date,
            'is_a2a': False,
            'requested_by': self.requested_by.id,
            'approved_by': self.approve_by.id,
            'approved_date': self.approve_date
        }

        return self.env['kr.purchase.order'].create([vals_list])

    # computed method
    def _compute_amount_total_est(self):
        veg_herb_line_total = self.sum_total_price(self.veg_herb_line_ids)
        fruit_line_total = self.sum_total_price(self.fruit_line_ids)
        poultry_line_total = self.sum_total_price(self.poultry_line_ids)
        sea_fish_line_total = self.sum_total_price(self.sea_fish_line_ids)
        beef_pork_line_total = self.sum_total_price(self.beef_pork_line_ids)
        other_line_total = self.sum_total_price(self.other_line_ids)

        self.amount_total_est = veg_herb_line_total + fruit_line_total + poultry_line_total + sea_fish_line_total + \
                                beef_pork_line_total + other_line_total
