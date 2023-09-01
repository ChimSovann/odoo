from odoo import fields, api, models


class ResPartner(models.Model):
  _inherit = 'res.partner'

  eng_name = fields.Char(string='Name', index=True)
  khmer_name = fields.Char(string='Khmer Name', index=True)

  @api.depends("firstname", "lastname", 'eng_name', 'khmer_name')
  def _compute_name(self):
    """Write the 'name' field according to splitted data."""
    for record in self:
      if not record.is_company:
        record.name = record._get_computed_name(record.lastname, record.firstname) + " " + str(record.khmer_name or '')
      else:
        record.name = str(record.eng_name or '') + " " + str(record.khmer_name or '')
