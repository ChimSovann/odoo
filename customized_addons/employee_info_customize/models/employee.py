from odoo import fields, models


class Employee(models.Model):
    _inherit = 'hr.employee'

    employee_id = fields.Char(stirng="Employee ID", help="អត្តលេខរបស់បុគ្គលិក \n Employee's ID")
    employee_nssf_id = fields.Char(string="NSSF ID", help="អត្តលេខ បសស"
                                                          "\n National Social Security Fund Id for employees")
    join_date = fields.Date(string="Join Date", required=True, help="ថ្ងៃដែលបុគ្គលិកចូលបម្រើការងារ"
                                                                    "\n Date that employee join the company")
    kh_name = fields.Char(string="Khmer Name")
    new_private_email = fields.Char(string="Private Email", help="Employee's personal email")
    private_phone = fields.Char(string="Private Phone", help="Employee's personal phone number")
    marriage_allowance = fields.Boolean(string="Marriage Allowance", help="Check: ប្តី/ប្រពន្ធមិនធ្វើការរដ្ឋបាល "
                                                                          "Spouse is not working under government \n "
                                                                          "Uncheck: ប្តី/ប្រពន្ធធ្វើការរដ្ឋបាល Spouce "
                                                                          "works "
                                                                          "under government")
