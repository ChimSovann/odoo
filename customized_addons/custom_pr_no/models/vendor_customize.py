from odoo import fields, api, models


class VendorCustomize(models.Model):
  _inherit = 'res.partner'

  internal_ref = fields.Char(string='Internal Reference', index=True, copy=False)
  internal_ref_customer = fields.Char(string='Internal Reference', index=True, copy=False)

  _sql_constraints = [
    ('internal_ref_uniq', 'unique(internal_ref)', "This reference code is already exist!"),
    ('internal_ref_customer_uniq', 'unique(internal_ref_customer)', "This reference code is already exist!")
  ]


  @api.depends("firstname", "lastname", 'eng_name', 'khmer_name', 'internal_ref', 'internal_ref_customer')
  def _compute_name(self):
    """Write the 'name' field according to splitted data."""
    for record in self:
      if not record.is_company:
        record.name = str(record.internal_ref_customer or '') + str(record.internal_ref or '') + " " + str(
          record.khmer_name or '') + " " + record._get_computed_name(record.lastname, record.firstname)
      else:
        record.firstname = record.eng_name or record.khmer_name or record.internal_ref or record.internal_ref_customer
        record.name = str(record.internal_ref_customer or '') + str(record.internal_ref or '') + " " + str(record.khmer_name or '') + " " + str(
          record.eng_name or '')