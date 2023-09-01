from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductReference(models.Model):
    _inherit = "product.category"

    reference_sequence = fields.Many2one('ir.sequence', string='Entry Sequence',)

class ProductSequence(models.Model):
    _inherit = "product.template"

    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True, default='/')


    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['default_code', 'categ_id'])
        for vals in vals_list:
            sequence_type = self.env['product.category'].browse(vals.get('categ_id', defaults.get('categ_id')))
            if vals.get('default_code', '/') == '/' and defaults.get('default_code', '/') == '/' and vals.get('categ_id', defaults.get('categ_id')):
                if sequence_type.reference_sequence:
                    vals['default_code'] = sequence_type.reference_sequence.next_by_id()


        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        templates = super(ProductSequence, self).create(vals_list)
        if "create_product_product" not in self._context:
            templates._create_variant_ids()

        # This is needed to set given values to first variant after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            if vals.get('barcode'):
                related_vals['barcode'] = vals['barcode']
            if vals.get('default_code'):
                related_vals['default_code'] = vals['default_code']
            if vals.get('standard_price'):
                related_vals['standard_price'] = vals['standard_price']
            if vals.get('volume'):
                related_vals['volume'] = vals['volume']
            if vals.get('weight'):
                related_vals['weight'] = vals['weight']
            # Please do forward port
            if vals.get('packaging_ids'):
                related_vals['packaging_ids'] = vals['packaging_ids']
            if related_vals:
                template.write(related_vals)

        return templates
