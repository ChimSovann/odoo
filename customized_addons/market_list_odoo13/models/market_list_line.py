from odoo import models, fields, api


class BaseMarketListRequestLine(models.AbstractModel):
    _name = 'base.market.list.request.line'
    _description = """
        this is a base model to inherit for creating request line model for requests models
        
        for:
        -> market.list.request.breakfast.day1.line
        -> market.list.request.lunch.day1.line
        -> market.list.request.dinner.day1.line
        -> market.list.request.drystore.day1.line
        -> market.list.request.breakfast.day2.line
        -> market.list.request.lunch.day2.line
        -> market.list.request.dinner.day2.line
        -> market.list.request.drystore.day2.line
            
        these model above are for tree view selection and connected by relation field
        inside market.list.request form view.

    """

    # defaults functions
    def _get_default_currency(self):
        currency = self.env['res.currency'].search([('name', '=', 'KHR')])
        return currency.id

    name = fields.Char('Description',
                       size=256,
                       tracking=True)

    price_per_unit_est = fields.Float('Estimated Price', required=True)

    total_price_est = fields.Float('Estimated Total Price',
                                   readonly=True,
                                   compute='_compute_total_price_est'
                                   )

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=[
                                     ('categ_id.parent_id.name', '=', 'Market List')]
                                 )

    product_type = fields.Char("Product Type", compute="_onchange_product_identifier")

    product_uom_id = fields.Many2one('uom.uom', 'Unit', required=True)

    product_qty = fields.Float('Quantity',
                               tracking=True,
                               digits='Product Unit of Measure',
                               required=True)

    currency_id = fields.Many2one('res.currency',
                                  "Currency",
                                  required=True,
                                  default=_get_default_currency,
                                  domain=[('name', 'in', ('USD', 'KHR'))])

    supplier_id = fields.Many2one('kirirom.supplier',
                                  'Kirirom Supplier')

    # this many2one field is default to market.list.request, you need to override this field if you want
    # use this for other lines model
    request_id = fields.Many2one('market.list.request',
                                 'Market List Request',
                                 ondelete='cascade', readonly=True)

    @api.depends('price_per_unit_est', 'product_qty')
    def _compute_total_price_est(self):
        for line in self:
            line.total_price_est = line.product_qty * line.price_per_unit_est

    @api.onchange('product_id')
    def onchange_product_uom(self):
        # setting unit field to the product_id unit
        self.product_uom_id = self.product_id.uom_id.id
        if self.product_id.survey_line_ids:
            # get the latest week record of survey price of the product
            # sorting the records to get the latest week
            sorted_lines = self.product_id.survey_line_ids.sorted(
                key=lambda x: x.date_start,
                reverse=True
            )
            survey_line_id = sorted_lines[0]
            self.price_per_unit_est = survey_line_id.price
            self.currency_id = survey_line_id.currency_id.id
            self.supplier_id = survey_line_id.supplier_id.id

    @api.onchange('product_id')
    def _onchange_product_identifier(self):
        for line in self:
            if line.product_id.type == "product":
                line.product_type = "Storable Product"
            elif line.product_id.type == "consu":
                line.product_type = "Consumable"
            elif line.product_id.type == "service":
                line.product_type = "Service"
            else:
                line.product_type = "N/A"


# market list request lines

class MarketListRequestBreakfastDay1(models.Model):
    _name = 'market.list.request.breakfast.day1.line'
    _inherit = ['base.market.list.request.line']


class MarketListRequestLunchDay1(models.Model):
    _name = 'market.list.request.lunch.day1.line'
    _inherit = ['base.market.list.request.line']


class MarketListRequestDinnerDay1(models.Model):
    _name = 'market.list.request.dinner.day1.line'
    _inherit = ['base.market.list.request.line']


class MarketListRequestDrystoreDay1Line(models.Model):
    _name = 'market.list.request.drystore.day1.line'
    _inherit = ['base.market.list.request.line']


class MarketListRequestBreakfastDay2(models.Model):
    _name = 'market.list.request.breakfast.day2.line'
    _inherit = ['base.market.list.request.line']


class MarketListRequestLunchDay2(models.Model):
    _name = 'market.list.request.lunch.day2.line'
    _inherit = ['base.market.list.request.line']


class MarketListRequestDinnerDay2(models.Model):
    _name = 'market.list.request.dinner.day2.line'
    _inherit = ['base.market.list.request.line']


class MarketListRequestDrystoreDay2Line(models.Model):
    _name = 'market.list.request.drystore.day2.line'
    _inherit = ['base.market.list.request.line']


class MarketListRequestGeneralLine(models.Model):
    _name = 'market.list.request.general.line'
    _inherit = ['base.market.list.request.line']

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=[]
                                 )

    request_id = fields.Many2one('market.list.general.request',
                                 'Market List Request',
                                 ondelete='cascade',
                                 readonly=True
                                 )


class MartketListRequestA2AGeneralLine(models.Model):
    _name = 'market.list.request.general.a2a.line'
    _inherit = ['base.market.list.request.line']

    request_id = fields.Many2one('market.list.general.a2a.request',
                                 'Market List Request',
                                 ondelete='cascade', readonly=True)

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=[]
                                 )
