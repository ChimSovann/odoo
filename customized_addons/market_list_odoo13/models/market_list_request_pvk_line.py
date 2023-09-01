from odoo import models, fields


class BaseMarketListPvkRequestLine(models.AbstractModel):
    _name = 'base.market.list.pvk.request.line'
    _inherit = ['base.market.list.request.line']
    _description = """
            this base model is a modified abstract base line model for pvk request line model
            
            for:
                -> market.list.pvk.request.vegetable.and.herb.line
                -> market.list.pvk.request.fruit.line
                -> market.list.pvk.request.poultry.line
                -> market.list.pvk.request.seafood.and.fish.line
                -> market.list.pvk.request.beef.and.pork.line
                -> market.l ist.pvk.request.other.line
                    
            these model above are for tree view selection and connected by relation field
            inside market.list.pvk.request form view.
        """

    request_id = fields.Many2one('market.list.pvk.request',
                                 'Pine View Kitchen',
                                 ondelete='cascade',
                                 readonly=True
                                 )


class MarketListPvkRequestVegetableAndHerbLine(models.Model):
    _name = 'market.list.pvk.request.vegetable.and.herb.line'
    _inherit = ['base.market.list.pvk.request.line']

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=['&',
                                         ('categ_id.parent_id.name', '=', 'Market List'),
                                         ('categ_id.name', '=', 'VEGETABLES & HERBS')]
                                 )


class MarketListPvkRequestFruitLine(models.Model):
    _name = 'market.list.pvk.request.fruit.line'
    _inherit = ['base.market.list.pvk.request.line']

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=['&',
                                         ('categ_id.parent_id.name', '=', 'Market List'),
                                         ('categ_id.name', '=', 'Fruit')]
                                 )


class MarketListPvkRequestPoultryLine(models.Model):
    _name = 'market.list.pvk.request.poultry.line'
    _inherit = ['base.market.list.pvk.request.line']

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=['&',
                                         ('categ_id.parent_id.name', '=', 'Market List'),
                                         ('categ_id.name', '=', 'Poultry')]
                                 )


class MarketListPvkRequestSeafoodAndFishLine(models.Model):
    _name = 'market.list.pvk.request.seafood.and.fish.line'
    _inherit = ['base.market.list.pvk.request.line']

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=['&',
                                         ('categ_id.parent_id.name', '=', 'Market List'),
                                         ('categ_id.name', 'in', ['SEA FOOD', 'Fish'])]
                                 )


class MarketListPvkRequestBeefAndPorkLine(models.Model):
    _name = 'market.list.pvk.request.beef.and.pork.line'
    _inherit = ['base.market.list.pvk.request.line']

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=['&',
                                         ('categ_id.parent_id.name', '=', 'Market List'),
                                         ('categ_id.name', 'in', ['Pork', 'Beef'])]
                                 )


class MarketListPvkRequestOtherLine(models.Model):
    _name = 'market.list.pvk.request.other.line'
    _inherit = ['base.market.list.pvk.request.line']

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 tracking=True,
                                 required=True,
                                 domain=['&',
                                         ('categ_id.parent_id.name', '=', 'Market List'),
                                         ('categ_id.name', 'in',
                                          ['Others', 'Dry food', 'Non dry food', 'Rice for student'])
                                         ]
                                 )
