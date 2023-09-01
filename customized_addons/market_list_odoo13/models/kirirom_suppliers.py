from odoo import models, fields, api
import re
from odoo.exceptions import ValidationError


class KiriromSuppliers(models.Model):

    _name = 'kirirom.supplier'
    _description = 'Kirirom supplier is used for creating the product for each supplier '

    name = fields.Char('Name', required=True)
    tel = fields.Char('Telephone')
    supplier_id = fields.Char('Id')
    product_ids = fields.Many2many('product.template', 'kirirom_supplier_products',
                                   'supplier_id', 'product_id',
                                   string='Products')

    # @api.constrains('tel')
    # def phone_num_validator(self):
    #     validate = re.match('^(0)[0-9]{8,9}$', self.tel)
    #     if not validate:
    #         raise ValidationError("Invalid Phone Number")
