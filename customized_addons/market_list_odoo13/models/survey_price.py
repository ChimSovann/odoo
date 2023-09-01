from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
from datetime import date, timedelta, datetime


class SurveyPrice(models.Model):
    _name = 'survey.price'

    name = fields.Char('Name', size=256, readonly=True)
    date_start = fields.Date('Start Date', required=True)

    def _get_default_currency(self):
        currency = self.env['res.currency'].search([('name', '=', 'KHR')])
        return currency.id

    @api.model
    def _get_default_lines(self):
        kirirom_supplier_model = self.env['kirirom.supplier'].search([])
        product_container = []
        for supplier in kirirom_supplier_model:
            for product in supplier.product_ids:
                product_container.append([0, False,
                                          {'currency_id': self._get_default_currency(),
                                           'price': 0,
                                           'supplier_id': supplier.id,
                                           'product_id': product.id}])

        return product_container

    lines = fields.One2many('survey.price.line',
                            'survey_price_id',
                            default=_get_default_lines,
                            string="Line ID",
                            required=True)

    def view_supplier_line(self):
        view_id_tree = self.env['ir.ui.view'].search(
            [('name', '=', 'survey.price.line.tree')])[0].id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Supplier Line'),
            'res_model': 'survey.price.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id_tree, 'tree'), (False, 'form')],
            'target': 'current',
            'domain': [('survey_price_id.id', '=', self.id)]
        }

    def write(self,
              vals):
        if vals.get('date_start'):
            raise except_orm(_('Warning'), _("You cannot Change Start Date"))
        return super(SurveyPrice, self).write(vals)

    @api.model
    def create(self,
               vals):
        day = datetime.strptime(vals['date_start'], "%Y-%m-%d")
        vals['name'] = str(day.year) + "/" + "Week" + str(day.isocalendar()[1])
        for survey in self.search([]):
            if survey.name == vals['name']:
                raise except_orm(_('Warning'), _("%s Already Exist!" % survey.name))
        return super(SurveyPrice, self).create(vals)

    def copy(self,
             default=None):
        default = dict(default or {})
        date_start = str(date.today())
        default.update({
            'date_start': date_start,
            'lines': [[0, False,
                       {'currency_id': line.currency_id.id, 'price': line.price, 'supplier_id': line.supplier_id.id,
                        'product_id': line.product_id.id}] for line in self.lines]
        })
        return super(SurveyPrice, self).copy(default)

    def unlink(self):
        for sp in self:
            for line in sp.lines:
                line.unlink()
        return super(SurveyPrice, self).unlink()

    @api.model
    def _get_default_date_start(self):
        return date.today() - timedelta(date.today().isocalendar()[2] - 1)

    _defaults = {
        'lines': _get_default_lines,
        'date_start': _get_default_date_start,
    }


class SurveyPriceLine(models.Model):
    _name = 'survey.price.line'

    survey_price_id = fields.Many2one('survey.price', "Survey Price Name", required=True)
    supplier_id = fields.Many2one('kirirom.supplier', "Kirirom Supplier", required=True)
    product_id = fields.Many2one('product.template', "Product")
    date_start = fields.Date('Start Date', related="survey_price_id.date_start", store=True, readonly=True)
    price = fields.Float('Price', required=True)
    price_khr = fields.Float('Price(KHR)', compute='_compute_price_khr', readonly=True, store=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', related='product_id.uom_id')
    currency_id = fields.Many2one('res.currency', "Currency", default=2, domain=[('name', 'in', ('USD', 'KHR'))])

    @api.depends('price', 'currency_id')
    def _compute_price_khr(self):
        for line in self:
            if line.currency_id.id == 66:
                line.price_khr = line.price
            elif line.currency_id.id == 3:
                line.price_khr = line.price * 4000


class KiriromProduct(models.Model):
    _inherit = "product.template"

    survey_line_ids = fields.One2many('survey.price.line', 'product_id', "Survey Line iD")
    supplier_ids = fields.Many2many('kirirom.supplier', 'kirirom_supplier_products', 'product_id',
                                    'supplier_id',
                                    string='Kirirom Supplier',
                                    help='List of Supplier.')
