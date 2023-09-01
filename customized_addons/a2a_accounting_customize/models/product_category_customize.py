from odoo import models, fields


class ProductCategory(models.Model):
  _inherit = 'product.category'
  # Create fields

  product_kh_name = fields.Char(string='Khmer Name')
  customer_discount_account_categ_id = fields.Many2one('account.account',
                                                       company_dependent=True,
                                                       string="Customer Discount Account",
                                                       domain="['&', ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
                                                       help="This account will be used when validating a customer discount.")
  fb_account = fields.Many2one('account.account', company_dependent=True,
                               string="F&B Account",
                               domain="[('internal_type', '=', 'other'), ('deprecated', '=', False), ('is_parent', '=', False)]",
                               help="This account will be used instead of the default one as the income account for hotel folio product")