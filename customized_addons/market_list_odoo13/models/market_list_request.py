from odoo import models, fields, api
import datetime


class MarketListRequest(models.Model):
    _name = 'market.list.request'
    _description = 'Market List Request'
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
                                    readonly=True,
                                    )

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
                                  readonly=True
                                  )

    # Purchase date field
    # # -> Day 1
    purchase_for_date_day1 = fields.Date('Purchase for date',
                                         required=True,
                                         states={'approved': [('readonly', True)],
                                                 'done': [('readonly', True)]}
                                         )
    # # -> Day 2
    purchase_for_date_day2 = fields.Date('Purchase for date',
                                         required=True,
                                         states={'approved': [('readonly', True)],
                                                 'done': [('readonly', True)]}
                                         )

    # price estimation fields for each menu
    # # -> Day 1
    breakfast_est_day1 = fields.Integer('Breakfast Estimation (pax)',
                                        states={'approved': [('readonly', True)],
                                                'done': [('readonly', True)]})
    lunch_est_day1 = fields.Integer('Lunch Estimation (pax)',
                                    states={'approved': [('readonly', True)],
                                            'done': [('readonly', True)]}
                                    )
    dinner_est_day1 = fields.Integer('Dinner Estimation (pax)',
                                     states={'approved': [('readonly', True)],
                                             'done': [('readonly', True)]}
                                     )
    total_est_day1 = fields.Integer('Total Estimation (pax)',
                                    states={'approved': [('readonly', True)],
                                            'done': [('readonly', True)]},
                                    default=0.0,
                                    compute='_compute_total_est_day1'
                                    )
    # # -> Day 2
    breakfast_est_day2 = fields.Integer('Breakfast Estimation (pax)',
                                        states={'approved': [('readonly', True)],
                                                'done': [('readonly', True)]})
    lunch_est_day2 = fields.Integer('Lunch Estimation (pax)',
                                    states={'approved': [('readonly', True)],
                                            'done': [('readonly', True)]}
                                    )
    dinner_est_day2 = fields.Integer('Dinner Estimation (pax)',
                                     states={'approved': [('readonly', True)],
                                             'done': [('readonly', True)]}
                                     )
    total_est_day2 = fields.Integer('Total Estimation (pax)',
                                    states={'approved': [('readonly', True)],
                                            'done': [('readonly', True)]},
                                    default=0.0,
                                    compute='_compute_total_est_day2'
                                    )

    # tree line relation fields and estimate price field for each line for purchase day 1
    # -> line ids fields for tree view inside the form request
    # # -> Day 1
    line_ids_day1_breakfast = fields.One2many('market.list.request.breakfast.day1.line',
                                              'request_id',
                                              'Breakfast - Day1',
                                              states={'approved': [('readonly', True)],
                                                      'done': [('readonly', True)]},
                                              copy=True)

    line_ids_day1_lunch = fields.One2many('market.list.request.lunch.day1.line',
                                          'request_id',
                                          'Lunch - Day1',
                                          states={'approved': [('readonly', True)],
                                                  'done': [('readonly', True)]},
                                          copy=True)

    line_ids_day1_dinner = fields.One2many('market.list.request.dinner.day1.line',
                                           'request_id',
                                           'Dry Store - Day1',
                                           states={'approved': [('readonly', True)],
                                                   'done': [('readonly', True)]},
                                           copy=True)

    dry_store_line_day1 = fields.One2many('market.list.request.drystore.day1.line',
                                          'request_id',
                                          'Dinner - Day1',
                                          states={'approved': [('readonly', True)],
                                                  'done': [('readonly', True)]},
                                          copy=True)
    # # -> Day 2
    line_ids_day2_breakfast = fields.One2many('market.list.request.breakfast.day2.line',
                                              'request_id',
                                              'Breakfast - Day2',
                                              states={'approved': [('readonly', True)],
                                                      'done': [('readonly', True)]},
                                              copy=True)

    line_ids_day2_lunch = fields.One2many('market.list.request.lunch.day2.line',
                                          'request_id',
                                          'Lunch - Day2',
                                          states={'approved': [('readonly', True)],
                                                  'done': [('readonly', True)]},
                                          copy=True)

    line_ids_day2_dinner = fields.One2many('market.list.request.dinner.day2.line',
                                           'request_id',
                                           'Dry Store - Day2',
                                           states={'approved': [('readonly', True)],
                                                   'done': [('readonly', True)]},
                                           copy=True)

    dry_store_line_day2 = fields.One2many('market.list.request.drystore.day2.line',
                                          'request_id',
                                          'Dinner - Day2',
                                          states={'approved': [('readonly', True)],
                                                  'done': [('readonly', True)]},
                                          copy=True)

    # -> total estimate price fields for each line ids view
    # # -> Day 1
    amount_total_est_breakfast_day1 = fields.Float(string='Exp. Subtotal',
                                                   readonly=True,
                                                   compute='_compute_amount_total_est_breakfast_day1')

    amount_total_est_lunch_day1 = fields.Float(string='Exp. Subtotal',
                                               readonly=True,
                                               compute='_compute_amount_total_est_lunch_day1')

    amount_total_est_dinner_day1 = fields.Float(string='Exp. Subtotal',
                                                readonly=True,
                                                compute='_compute_amount_total_est_dinner_day1')

    amount_total_est_dry_store_day1 = fields.Float(string='Exp. Subtotal',
                                                   readonly=True,
                                                   compute='_compute_amount_total_est_dry_store_day1')
    # # -> Day 2
    amount_total_est_breakfast_day2 = fields.Float(string='Exp. Subtotal',
                                                   readonly=True,
                                                   compute='_compute_amount_total_est_breakfast_day2')

    amount_total_est_lunch_day2 = fields.Float(string='Exp. Subtotal',
                                               readonly=True,
                                               compute='_compute_amount_total_est_lunch_day2')

    amount_total_est_dinner_day2 = fields.Float(string='Exp. Subtotal',
                                                readonly=True,
                                                compute='_compute_amount_total_est_dinner_day2')

    amount_total_est_dry_store_day2 = fields.Float(string='Exp. Subtotal',
                                                   readonly=True,
                                                   compute='_compute_amount_total_est_dry_store_day2')

    # budget per pax and grand total estimate section
    # # -> Day 1
    budget_per_pax_day1 = fields.Float(string='Budget/Pax',
                                       readonly=True,
                                       default=0.0,
                                       compute='_compute_budget_per_pax_day1'
                                       )

    grand_total_est_day1 = fields.Float(string='Exp. Grand Total',
                                        readonly=True,
                                        compute='_compute_grand_total_est_day1'
                                        )
    # # -> Day 2
    budget_per_pax_day2 = fields.Float(string='Budget/Pax',
                                       readonly=True,
                                       default=0.0,
                                       compute='_compute_budget_per_pax_day2'
                                       )

    grand_total_est_day2 = fields.Float(string='Exp. Grand Total',
                                        readonly=True,
                                        compute='_compute_grand_total_est_day2')

    # menu description fields
    # # -> Day 1
    breakfast_description_day1 = fields.Text('Breakfast Menu',
                                             states={'approved': [('readonly', True)],
                                                     'done': [('readonly', True)]})
    lunch_description_day1 = fields.Text('Lunch Menu',
                                         states={'approved': [('readonly', True)],
                                                 'done': [('readonly', True)]})
    dinner_description_day1 = fields.Text('Dinner Menu',
                                          states={'approved': [('readonly', True)],
                                                  'done': [('readonly', True)]})
    # # -> Day 2
    breakfast_description_day2 = fields.Text('Breakfast Menu',
                                             states={'approved': [('readonly', True)],
                                                     'done': [('readonly', True)]})
    lunch_description_day2 = fields.Text('Lunch Menu',
                                         states={'approved': [('readonly', True)],
                                                 'done': [('readonly', True)]})
    dinner_description_day2 = fields.Text('Dinner Menu',
                                          states={'approved': [('readonly', True)],
                                                  'done': [('readonly', True)]})

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

    # super functions section
    @api.model
    def create(self,
               vals_list):
        # converting vals_list into object just to make sure because
        # in the odoo document they mentioned that it could be type dict or list
        vals_list = dict(vals_list or {})
        # updating name field to a unique sequence for this record
        vals_list['name'] = self.env['ir.sequence'].next_by_code('market.list.request.sequence')
        # setting the creation date for the request
        vals_list['creation_date'] = datetime.datetime.today()
        # I use "[vals_list]" instead of just "vals_list" because the create function take list as an argument
        record = super(MarketListRequest, self).create([vals_list])
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
        record = super(MarketListRequest, self).write(vals)
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
        return super(MarketListRequest, self).copy(default)

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
        date_order = datetime.datetime.today()

        # list for storing all selected product for each menu
        breakfast_day1, lunch_day1, dinner_day1, dry_store_day1 = [], [], [], []
        breakfast_day2, lunch_day2, dinner_day2, dry_store_day2 = [], [], [], []

        # length of each menu lines
        breakfast_day1_length = len(self.line_ids_day1_breakfast)
        lunch_day1_length = len(self.line_ids_day1_lunch)
        dinner_day1_length = len(self.line_ids_day1_dinner)
        dry_store_day1_length = len(self.dry_store_line_day1)
        breakfast_day2_length = len(self.line_ids_day2_breakfast)
        lunch_day2_length = len(self.line_ids_day2_lunch)
        dinner_day2_length = len(self.line_ids_day2_dinner)
        dry_store_day2_length = len(self.dry_store_line_day2)

        # find the max time to run the for loop
        max_length = max([
            breakfast_day1_length,
            breakfast_day2_length,
            lunch_day1_length,
            lunch_day2_length,
            dinner_day1_length,
            dinner_day2_length,
            dry_store_day1_length,
            dry_store_day2_length,
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
                    'supplier_id': product.supplier_id.id,
                    'currency_id': product.currency_id.id,
                    'price_per_unit': product.price_per_unit_est
                }])

        for index in range(0, max_length):
            add_item(index, breakfast_day1_length, breakfast_day1, self.line_ids_day1_breakfast)
            add_item(index, lunch_day1_length, lunch_day1, self.line_ids_day1_lunch)
            add_item(index, dinner_day1_length, dinner_day1, self.line_ids_day1_dinner)
            add_item(index, dry_store_day1_length, dry_store_day1, self.dry_store_line_day1)
            add_item(index, breakfast_day2_length, breakfast_day2, self.line_ids_day2_breakfast)
            add_item(index, lunch_day2_length, lunch_day2, self.line_ids_day2_lunch)
            add_item(index, dinner_day2_length, dinner_day2, self.line_ids_day2_dinner)
            add_item(index, dry_store_day2_length, dry_store_day2, self.dry_store_line_day2)

        order_line = breakfast_day1 + lunch_day1 + dinner_day1 + dry_store_day1 + \
                     breakfast_day2 + lunch_day2 + dinner_day2 + dry_store_day2

        # TODO: not finished yet and i still couldn't figure where is the new_array use for
        # this code loop thru every item inside order_list and combine the selected item whose is the same
        # into one item
        new_array = []
        for menu in order_line:
            if len(new_array) == 0:
                new_array.append(menu)
            else:
                is_append = 1
                selected_menu = menu[2]
                for item in new_array:
                    food_item = item[2]
                    if selected_menu['product_id'] == food_item['product_id']:
                        is_append = 0
                        food_item['product_qty'] += selected_menu['product_qty']
                if is_append == 0:
                    continue
                else:
                    new_array.append(menu)

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

    # compute functions section fields

    # -> price estimate per person for a day
    # # -> Day 1
    @api.depends('breakfast_est_day1', 'lunch_est_day1', 'dinner_est_day1')
    def _compute_total_est_day1(self):
        self.total_est_day1 = self.breakfast_est_day1 + self.lunch_est_day1 + self.dinner_est_day1

    # # -> Day 2
    @api.depends('breakfast_est_day2', 'lunch_est_day2', 'dinner_est_day2')
    def _compute_total_est_day2(self):
        self.total_est_day2 = self.breakfast_est_day2 + self.lunch_est_day2 + self.dinner_est_day2

    # -> Tree line ids fields sections
    # # -> Day 1
    @api.onchange('line_ids_day1_breakfast')
    def _compute_amount_total_est_breakfast_day1(self):
        self.amount_total_est_breakfast_day1 = self.sum_total_price(self.line_ids_day1_breakfast)

    @api.onchange('line_ids_day1_lunch')
    def _compute_amount_total_est_lunch_day1(self):
        self.amount_total_est_lunch_day1 = self.sum_total_price(self.line_ids_day1_lunch)

    @api.onchange('line_ids_day1_dinner')
    def _compute_amount_total_est_dinner_day1(self):
        self.amount_total_est_dinner_day1 = self.sum_total_price(self.line_ids_day1_dinner)

    @api.onchange('dry_store_line_day1')
    def _compute_amount_total_est_dry_store_day1(self):
        self.amount_total_est_dry_store_day1 = self.sum_total_price(self.dry_store_line_day1)

    # # -> Day 2
    @api.onchange('line_ids_day2_breakfast')
    def _compute_amount_total_est_breakfast_day2(self):
        self.amount_total_est_breakfast_day2 = self.sum_total_price(self.line_ids_day2_breakfast)

    @api.onchange('line_ids_day2_lunch')
    def _compute_amount_total_est_lunch_day2(self):
        self.amount_total_est_lunch_day2 = self.sum_total_price(self.line_ids_day2_lunch)

    @api.onchange('line_ids_day2_dinner')
    def _compute_amount_total_est_dinner_day2(self):
        self.amount_total_est_dinner_day2 = self.sum_total_price(self.line_ids_day2_dinner)

    @api.onchange('dry_store_line_day2')
    def _compute_amount_total_est_dry_store_day2(self):
        self.amount_total_est_dry_store_day2 = self.sum_total_price(self.dry_store_line_day2)

    # -> grand total estimate and budget per pax
    # # -> Day 1
    @api.depends('amount_total_est_breakfast_day1', 'amount_total_est_lunch_day1',
                 'amount_total_est_dinner_day1', 'amount_total_est_dry_store_day1')
    def _compute_grand_total_est_day1(self):
        # this function use for sum up all the total for the lines for day 1
        #
        # the slash '\' right here use to break to a new line of code instead of writing one long line of code
        self.grand_total_est_day1 = self.amount_total_est_breakfast_day1 + \
                                    self.amount_total_est_lunch_day1 + \
                                    self.amount_total_est_dinner_day1 + \
                                    self.amount_total_est_dry_store_day1

    @api.onchange('grand_total_est_day1', 'total_est_day1')
    def _compute_budget_per_pax_day1(self):
        # I'm rewriting the codebase from the senior and I have no clue what is function does lmao.
        count = 0
        budget_per_pax = 0.0

        if self.breakfast_est_day1:
            count += 1
        if self.lunch_est_day1:
            count += 1
        if self.dinner_est_day1:
            count += 1
        if self.total_est_day1:
            budget_per_pax = self.grand_total_est_day1 * count / self.total_est_day1
        else:
            budget_per_pax = 0.0
        self.budget_per_pax_day1 = budget_per_pax

    # # -> Day 2
    @api.depends('amount_total_est_breakfast_day2', 'amount_total_est_lunch_day2',
                 'amount_total_est_dinner_day2', 'amount_total_est_dry_store_day2')
    def _compute_grand_total_est_day2(self):
        # this function use for sum up all the total for the lines for day 2
        #
        # the slash '\' right here use to break to a new line of code instead of writing one long line of code
        self.grand_total_est_day2 = self.amount_total_est_breakfast_day2 + \
                                    self.amount_total_est_lunch_day2 + \
                                    self.amount_total_est_dinner_day2 + \
                                    self.amount_total_est_dry_store_day2

    @api.onchange('grand_total_est_day2', 'total_est_day2')
    def _compute_budget_per_pax_day2(self):
        # I'm rewriting the codebase from the senior and I have no clue what is function does lmao.
        # and yes I copied and pasted this line of comment from above
        # I hope you have a good day reading my code LOL
        count = 0
        budget_per_pax = 0.0

        if self.breakfast_est_day2:
            count += 1
        if self.lunch_est_day2:
            count += 1
        if self.dinner_est_day2:
            count += 1
        if self.total_est_day2:
            budget_per_pax = self.grand_total_est_day2 * count / self.total_est_day2
        else:
            budget_per_pax = 0.0
        self.budget_per_pax_day2 = budget_per_pax
