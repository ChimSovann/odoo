from datetime import timedelta

from odoo import models, fields, api, _
from odoo.tools import float_is_zero


# Inherit hotel.folio Model to add some new fields
class HotelReceiptNo(models.Model):
    _inherit = 'hotel.folio'

    receipt_no = fields.Char(string="Receipt No", readonly=True, states={'draft': [('readonly', False)]})
    ref_booking = fields.Char(string='Ref Booking')
    x_cambodian = fields.Integer(string="Cambodian")
    x_foreigner = fields.Integer(string="Foreigner")
    is_paid = fields.Boolean(string="Paid", compute="_check_is_paid")
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        "Branch",
        readonly=True,
        required=True,
        default=lambda self: self.env['stock.warehouse'].search([('code', '=', 'hotel')]),
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
    )
    
    customer_types = fields.Many2one(
        'hotel.customer.type',
        string='Customer Type', 
    )
    
    country_types = fields.Many2one(
        'hotel.country.type',
        string='Country',
    )
    
    city_types = fields.Many2one(
        'hotel.city.type',
        string='City',
    )

    

    # Check whether if the invoice paid or not
    def _check_is_paid(self):
        for record in self:
            invoice_payment_state = record.hotel_invoice_id["invoice_payment_state"]
            is_paid = True if invoice_payment_state == "paid" else False
            record.is_paid = is_paid

    # compute_button
    def compute_button(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            order = folio.order_id
            x = order.compute_button()
        return x

    def write(self, vals):
        product_obj = self.env["product.product"]
        h_room_obj = self.env["hotel.room"]
        folio_room_line_obj = self.env["folio.room.line"]
        res = False
        for rec in self:
            # res = super(HotelFolio, self).write(vals)
            rooms_list = [res.product_id.id for res in rec.room_line_ids]
            if vals and vals.get("duration_dummy", False):
                vals["duration"] = vals.get("duration_dummy", 0.0)
            else:
                vals["duration"] = rec.duration
            res = super(HotelReceiptNo, self).write(vals)
            for room_line in rec.room_line_ids:
                room_obj = h_room_obj.search([("name", "=", room_line.product_id.name)])
                folio_roomline_rec = folio_room_line_obj.search(
                    [("room_id", "=", room_obj.id), ("folio_id", "=", rec.id),
                     ("check_out", ">", room_line.checkout_date)]
                )

                if rec.checkout_date > room_line.checkout_date:
                    if len(folio_roomline_rec) != 0:
                        vals = {
                            "room_id": room_obj.id,
                            "check_in": room_line.checkin_date.replace(hour=00) + timedelta(hours=7),
                            "check_out": room_line.checkout_date.replace(hour=00) + timedelta(hours=5),
                            "folio_id": rec.id,
                        }
                        folio_roomline_rec.write(vals)
                    else:
                        vals = {
                            "room_id": room_obj.id,
                            "check_in": room_line.checkin_date.replace(hour=00) + timedelta(hours=7),
                            "check_out": room_line.checkout_date.replace(hour=00) + timedelta(hours=5),
                            "folio_id": rec.id,
                        }
                        folio_room_line_obj.create(vals)
                else:
                    folio_roomline_rec = folio_room_line_obj.search(
                        [("room_id", "=", room_obj.id), ("folio_id", "=", rec.id)]
                    )
                    vals = {
                        "room_id": room_obj.id,
                        "check_in": rec.checkin_date,
                        "check_out": rec.checkout_date,
                        "folio_id": rec.id,
                    }
                    folio_roomline_rec.create(vals)
        return res


# Inherit sale.order Model to add folio_ids field
class HotelReceiptNoInSale(models.Model):
    _inherit = 'sale.order'

    folio_ids = fields.One2many("hotel.folio", "order_id")

    # Overwrite _prepare_invoice() method to update invoice_vals using field get from hotel.folio Model
    def _prepare_invoice(self):
        invoice_vals = super(HotelReceiptNoInSale, self)._prepare_invoice()
        invoice_vals.update({
            'receipt_no': self.folio_ids.receipt_no,
            'fol_no_inv': self.folio_ids.name,
            'checkin': self.folio_ids.checkin_date,
            'checkout': self.folio_ids.checkout_date,
        })
        return invoice_vals

    def compute_button(self):
        return True


class CustomInvoiceWizard(models.Model):
    _inherit = 'account.payment'

    payment_ref = fields.Char(string='Payment Reference', readonly=True, states={'draft': [('readonly', False)]})
    analytic_id = fields.Many2one('account.analytic.account', 'Write-Off Analytic Account', readonly=True,
                                  states={'draft': [('readonly', False)]})


# Inherit account.move Model to add some new fields
class HotelReceiptNoInInvoice(models.Model):
    _inherit = 'account.move'

    receipt_no = fields.Char(string="Receipt No")
    fol_no_inv = fields.Char(string="Folio No")
    checkin = fields.Datetime(string='Checkin Date')
    checkout = fields.Datetime(string='Checkout Date')
    payment_ids = fields.Many2many('account.move.line', string='Payments', compute='_compute_payments')
    # x_rate = fields.Float(string="Exchange Rate(KHR)", store=True, states={'paid': [('readonly', True)]})
    x_amount_total_khmer = fields.Float(string='Total ( KHR )', store=True, readonly=True,
                                        compute='_compute_amount_total')
    khr_currency_id = fields.Many2one('res.currency', store=True, compute='_compute_amount_total')
    # account_id = fields.Many2one('account.account', string='Account',
    #                              required=True, readonly=True, states={'draft': [('readonly', False)]},
    #                              help="The partner account used for this invoice.")
    acc_id = fields.Many2one('account.account', company_dependent=True,
                    string="Account Receivable",
                    domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False), ('is_parent', '=', False)]",
                    help="This account will be used instead of the default one as the receivable account for the current partner")

    @api.depends('x_rate', 'amount_total')
    def _compute_amount_total(self):
        for rec in self:
            rec.x_amount_total_khmer = rec.amount_total * rec.x_rate
            rec.khr_currency_id = self.env['res.currency'].search([('id', '=', 66)])

    @api.returns('self')
    def _get_default_khr_exchange_currency(self):
        return self.env['res.currency'].search([('name', '=', 'KHR')], limit=1)
    khr_exchange_currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, required=True,
                                               states={'draft': [('readonly', False)]},
                                               default=_get_default_khr_exchange_currency)
    # khr_xcehange_rate = fields.Float('KHR Riel Exchange Rate', store=True, readonly=True,
    #                                  compute="_compute_khr_exchange_rate")
    x_rate = fields.Float('KHR Riel Exchange Rate', store=True, readonly=True,
                                     compute="_compute_khr_exchange_rate")

    @api.depends('khr_exchange_currency_id', 'date')
    def _compute_khr_exchange_rate(self):
        for move in self:
            currency_rates = move.khr_exchange_currency_id._get_rates(move.company_id, move.invoice_date or fields.Date.today())
            move.x_rate = currency_rates.get(move.khr_exchange_currency_id.id) or 1.0

    @api.depends('date')
    def _onchange_register_rate(self):
        self._compute_khr_exchange_rate

    def _compute_payments(self):
        for rec in self:
            rec.payment_ids = rec.env['account.move.line']
            foreign_currency = rec.currency_id if rec.currency_id != rec.company_id.currency_id else False
            pay_term_line_ids = rec.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            partials = pay_term_line_ids.mapped('matched_debit_ids') + pay_term_line_ids.mapped('matched_credit_ids')

            for partial in partials:
                counterpart_lines = partial.debit_move_id + partial.credit_move_id
                # In case we are in an onchange, line_ids is a NewId, not an integer. By using line_ids.ids we get the correct integer value.
                counterpart_line = counterpart_lines.filtered(lambda line: line.id not in rec.line_ids.ids)

                if foreign_currency and partial.currency_id == foreign_currency:
                    amount = partial.amount_currency
                else:
                    amount = partial.company_currency_id._convert(partial.amount, rec.currency_id, rec.company_id,
                                                                rec.date)

                if float_is_zero(amount, precision_rounding=rec.currency_id.rounding):
                    continue
                ref = counterpart_line.move_id.name
                if counterpart_line.move_id.ref:
                    ref += ' (' + counterpart_line.move_id.ref + ')'
                rec.payment_ids += counterpart_line
