from odoo import models, api
from lxml import etree


def update_domain(res, fields_to_update):
  for field in fields_to_update:
    if field in res:
      if isinstance(res[field]['domain'], list):
        new_domain = res[field]['domain'] + [('is_parent', '=', False)]
      else:
        new_domain = res[field]['domain'][:-1] + ", ('is_parent', '=', False)]"
      res[field]['domain'] = new_domain
  return res


class MarketListOrder(models.Model):
  _inherit = 'kr.purchase.order'

  @api.model
  def fields_get(self, allfields=None, attributes=None):
    res = super(MarketListOrder, self).fields_get(allfields, attributes)
    return update_domain(res, ['credit_acc', 'debit_acc'])


class MarketListOrderLine(models.Model):
  _inherit = 'kr.purchase.order.line'

  @api.model
  def fields_get(self, allfields=None, attributes=None):
    res = super(MarketListOrderLine, self).fields_get(allfields, attributes)
    return update_domain(res, ['debit_acc'])


class ProductTemplate(models.Model):
  _inherit = 'product.template'

  @api.model
  def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    res = super(ProductTemplate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
    doc_form = etree.XML(res['arch'])
    if view_type == 'form':  # Applies only for form view
      for node in doc_form.xpath("//field"):
        if node.get('name') == 'property_account_income_id':
          node.set('domain', "[('is_parent', '=', False), ('internal_type', '=', 'other'), ('deprecated', '=', False)]")
        elif node.get('name') in ['property_account_expense_id', 'property_account_creditor_price_difference']:
          node.set('domain', "[('deprecated', '=', False), ('is_parent', '=', False)]")

      res['arch'] = etree.tostring(doc_form)
    return res


class ProductProduct(models.Model):
  _inherit = 'product.product'

  @api.model
  def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    res = super(ProductProduct, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)
    doc_form = etree.XML(res['arch'])
    if view_type == 'form':  # Applies only for form view
      for node in doc_form.xpath("//field"):
        if node.get('name') == 'property_account_income_id':
          node.set('domain', "[('is_parent', '=', False), ('internal_type', '=', 'other'), ('deprecated', '=', False)]")
        elif node.get('name') in ['property_account_expense_id', 'property_account_creditor_price_difference']:
          node.set('domain', "[('deprecated', '=', False), ('is_parent', '=', False)]")

      res['arch'] = etree.tostring(doc_form)
    return res


class ProductCategory(models.Model):
  _inherit = 'product.category'

  @api.model
  def fields_get(self, allfields=None, attributes=None):
    res = super(ProductCategory, self).fields_get(allfields, attributes)
    return update_domain(res, ['property_account_creditor_price_difference', 'customer_discount_account_categ_id',
                               'property_stock_account_input_categ_id', 'property_stock_account_output_categ_id',
                               'property_stock_valuation_account_id'])

  @api.model
  def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    res = super(ProductCategory, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
    doc_form = etree.XML(res['arch'])
    if view_type == 'form':  # Applies only for form view
      for node in doc_form.xpath("//field"):
        if node.get('name') in ['property_account_income_categ_id', 'property_account_expense_categ_id']:
          node.set('domain', "[('is_parent', '=', False), ('internal_type', '=', 'other'), ('deprecated', '=', False)]")
        if node.get('name') == 'property_account_creditor_price_difference_categ':
          node.set('domain', "[('deprecated', '=', False), ('is_parent', '=', False)]")
      res['arch'] = etree.tostring(doc_form)
    return res


class POSPaymentMethod(models.Model):
  _inherit = 'pos.payment.method'

  @api.model
  def fields_get(self, allfields=None, attributes=None):
    res = super(POSPaymentMethod, self).fields_get(allfields, attributes)
    return update_domain(res, ['receivable_account_id'])


class ResPartner(models.Model):
  _inherit = 'res.partner'

  @api.model
  def fields_get(self, allfields=None, attributes=None):
    res = super(ResPartner, self).fields_get(allfields, attributes)
    return update_domain(res, ['property_account_receivable_id', 'property_account_payable_id'])


class AccTaxRepartitionLine(models.Model):
  _inherit = 'account.tax.repartition.line'

  @api.model
  def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    res = super(AccTaxRepartitionLine, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                             submenu=submenu)
    doc = etree.XML(res['arch'])
    if view_type == 'tree':  # Applies only for tree view
      for node in doc.xpath("//field"):
        if node.get('name') == 'account_id':
          node.set('domain', "[('internal_type', 'not in', ('receivable', 'payable')), ('is_parent', '=', False)]")
      res['arch'] = etree.tostring(doc)
    return res


class AccountJournal(models.Model):
  _inherit = 'account.journal'

  @api.model
  def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    res = super(AccountJournal, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)
    doc = etree.XML(res['arch'])
    if view_type == 'form':  # Applies only for form view
      for node in doc.xpath("//field"):
        if node.get('name') in ['default_credit_account_id', 'default_debit_account_id']:
          node.set('domain',
                   "[('deprecated', '=', False), ('is_parent', '=', False)]")
      res['arch'] = etree.tostring(doc)
    return res


class HRSalaryRule(models.Model):
  _inherit = 'hr.salary.rule'

  @api.model
  def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    res = super(HRSalaryRule, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                    submenu=submenu)
    doc = etree.XML(res['arch'])
    if view_type == 'form':  # Applies only for form view
      for node in doc.xpath("//field"):
        if node.get('name') in ['account_debit', 'account_credit']:
          node.set('domain',
                   "[('deprecated', '=', False), ('is_parent', '=', False)]")
      res['arch'] = etree.tostring(doc)
    return res
