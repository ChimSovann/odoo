from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from collections import defaultdict
from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re

from odoo.addons.account.models.account_move import AccountMove as OriginalAccountMove

def post(self):
    # `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
    if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
        raise AccessError(_("You don't have the access rights to post an invoice."))
    for move in self:
        if move.state == 'posted':
            raise UserError(_('The entry %s (id %s) is already posted.') % (move.name, move.id))
        if not move.line_ids.filtered(lambda line: not line.display_type):
            raise UserError(_('You need to add a line before posting.'))
        if move.auto_post and move.date > fields.Date.today():
            date_msg = move.date.strftime(get_lang(self.env).date_format)
            raise UserError(_("This move is configured to be auto-posted on %s" % date_msg))

        if not move.partner_id:
            if move.is_sale_document():
                raise UserError(
                    _("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
            elif move.is_purchase_document():
                raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

        if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0,
                                                                    precision_rounding=move.currency_id.rounding) < 0:
            raise UserError(_(
                "You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))

        # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
        # lines are recomputed accordingly.
        # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
        # environment.
        if not move.invoice_date and move.is_invoice(include_receipts=True):
            move.invoice_date = fields.Date.context_today(self)
            move.with_context(check_move_validity=False)._onchange_invoice_date()

        # When the accounting date is prior to the tax lock date, move it automatically to the next available date.
        # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
        # environment.
        if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (
                move.line_ids.tax_ids or move.line_ids.tag_ids):
            move.date = move.company_id.tax_lock_date + timedelta(days=1)
            move.with_context(check_move_validity=False)._onchange_currency()

    # Create the analytic lines in batch is faster as it leads to less cache invalidation.
    self.mapped('line_ids').create_analytic_lines()
    for move in self:
        if move.auto_post and move.date > fields.Date.today():
            raise UserError(_("This move is configured to be auto-posted on {}".format(
                move.date.strftime(get_lang(self.env).date_format))))
        #############
        # Start Modification
        #############

        if move.ref != '/':
            move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])

        #############
        # End Modification
        #############

        to_write = {'state': 'posted'}

        if move.name == '/':
            # Get the journal's sequence.
            sequence = move._get_sequence()
            if not sequence:
                raise UserError(_('Please define a sequence on your journal.'))

            # Consume a new number.
            to_write['name'] = sequence.with_context(ir_sequence_date=move.date).next_by_id()

        move.write(to_write)

        # Compute 'ref' for 'out_invoice'.
        if move.type == 'out_invoice' and not move.invoice_payment_ref:
            to_write = {
                'invoice_payment_ref': move._get_invoice_computed_reference(),
                'line_ids': []
            }
            for line in move.line_ids.filtered(
                    lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                to_write['line_ids'].append((1, line.id, {'name': to_write['invoice_payment_ref']}))
            move.write(to_write)

        if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
            # For opening moves, we set the reconciliation date threshold
            # to the move's date if it wasn't already set (we don't want
            # to have to reconcile all the older payments -made before
            # installing Accounting- with bank statements)
            move.company_id.account_bank_reconciliation_start = move.date

    for move in self:
        if not move.partner_id: continue
        partners = (move.partner_id | move.partner_id.commercial_partner_id)
        if move.type.startswith('out_'):
            partners._increase_rank('customer_rank')
        elif move.type.startswith('in_'):
            partners._increase_rank('supplier_rank')
        else:
            continue

    # Trigger action for paid invoices in amount is zero
    self.filtered(
        lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
    ).action_invoice_paid()

    # Force balance check since nothing prevents another module to create an incorrect entry.
    # This is performed at the very end to avoid flushing fields before the whole processing.
    self._check_balanced()
    return True

OriginalAccountMove.post = post


class VkPosOrder(models.Model):
    _name = "vk.pos.order"

    vendor = fields.Char("Vendor", states={'paid': [('readonly', True)]})
    name = fields.Char("name", readonly=True, index=True)
    items = fields.One2many('dummy.orders.line', 'vk_order_id', 'Order Lines')
    subtotal = fields.Float("Total", states={'paid': [('readonly', True)]})
    vat = fields.Float("VAT", states={'paid': [('readonly', True)]})
    total = fields.Float("Total(VAT included)", states={'paid': [('readonly', True)]})
    state = fields.Selection([('pending', 'PENDING'),
                              ('paid', 'PAID')], 'State', select=True,
                             required=True, readonly=True,
                             default=lambda *a: 'pending')
    remark = fields.Char('Remark', size=256)

    def post(self, data, context=None):
        """ post and broadcast a message, return the message id """
        print("Postingggg")
        channel_name = "vk.pos.order"
        self.env['pos.config'].sudo().send_to_all_poses(channel_name, data)
        self.env['bus.bus'].sendone("vk.pos.order", data)
        return True



class dummy_order_line(models.Model):
    _inherit = "dummy.orders.line"

    vk_order_id = fields.Many2one('vk.pos.order', string= 'VK Order Ref', ondelete='cascade')
    vk_data_id = fields.Many2one('vk.data', 'VK Data Ref', ondelete='cascade')
    uom = fields.Char('Unit of Measure')


