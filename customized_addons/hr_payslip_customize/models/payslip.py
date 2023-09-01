from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EmployeePayslip(models.Model):
    _inherit = 'hr.payslip'

    additional_allowance = fields.Float(string="Additional Allowance")
    exchange_rate = fields.Integer(string="Exchange Rate (GDT)", readonly=True, required=True,
                                   states={'draft': [('readonly', False)]})
    ot_weekday_150 = fields.Float(string="Overtime Weekday 150% (h)",
                                    help="ចំនួនម៉ោងធ្វើការបន្ថែម មុនម៉ោង១០យប់"
                                         "\n Number of Overtime Weekday in 'hours' before 10PM")
    ot_weekday_200 = fields.Float(string="Overtime Weekday 200% (h)",
                                    help="ចំនួនម៉ោងធ្វើការបន្ថែម បន្ទាប់ពីម៉ោង១០យប់"
                                         "\n Number of Overtime Weekday in 'hours' after 10PM")
    ot_ph = fields.Float(string="Overtime PH 100% (days)",
                           help="ចំនួនថ្ងៃធ្វើការបន្ថែម នៅថ្ងៃសម្រាកជាសាធារណៈ"
                                "\n Number of Overtime Public Holiday in 'Days'")
    ot_day_off = fields.Float(string="Overtime Day off 200% (days)",
                                help="ចំនួនថ្ងៃធ្វើការបន្ថែម នៅថ្ងៃអាទិត្យ ឬ ថ្ងៃឈប់សម្រាក"
                                     "\n Number of Overtime Sunday/Day-off in 'Days' ")
    remain_al = fields.Float(string="Remain AL (days)",
                               help="Number of Remain AL to calculate when that employee resign only")
    deduction = fields.Float(string="Deduction (days)", help="ប្រាក់កាត់កង \n Number of Deduction day")
    deduction_dollar = fields.Float(string="Deduction ($)", help="ប្រាក់កាត់កង(គិតជា$)")
    att_bonus = fields.Float(string="Attendance Bonus ($)", help="ប្រាក់រង្វាន់បន្ថែម"
                                                                   "\n Bonus amount for employee Salary in '$' ")
    incentive = fields.Float(string="Incentive ($)", help="ប្រាក់រង្វាន់លើកទឹកចិត្ត គិតជា'$' "
                                                            "\n Amount paid to an employee encourages to do something")
    mission = fields.Float(string="Mission Time ($)", help="ប្រាក់បេសកម្ម គិតជា'$' "
                                                             "\n Amount paid to an employee for any mission")
    senior_months = fields.Integer(string="Seniority Months", compute="_get_number_of_seniority_month",
                                   help="ចំនួនខែ/ថ្ងៃ ដែលបុគ្គលិកបានចូលបម្រើការងារ"
                                        "\n Number of Months/Days that employee worked in the company")
    senior_days = fields.Integer(string="Seniority Days", compute="_get_number_of_seniority_month")
    senior_bonus = fields.Float(string="Seniority Bonus ($)",
                                  help="ប្រាក់រង្វាន់អតីតភាពការងារ គិតជា'$'"
                                       "\n Amount paid to employee who worked more than 13 months")
    senior_payment = fields.Float(string="Seniority Payment ($)",
                                  help="ប្រាក់រំលឹកអតីតភាពការងារ គិតជា'$'"
                                       "\n Amount paid to employee every 6 months which equal to 7.5days")
    severance = fields.Float(string="Severance ($)", help="ប្រាក់បំណាច់កិច្ចសន្យាការងារ គិតជា'$' "
                                                          "\n Amount paid to an employee which equal to 5% in 1 year")
    other = fields.Float(string="Other ($)", help="ផ្សេងៗ គិតជា'$' \n Other Payment")
    employee_id = fields.Many2one('hr.employee', String='Employee')

    # to calculate seniority month base on 'join_date' field in employee_info
    @api.depends('employee_id')
    def _get_number_of_seniority_month(self):
        today_date = fields.Datetime.now()
        for employee in self:
            if employee.employee_id.join_date:
                join_date = fields.Datetime.to_datetime(employee.employee_id.join_date)
                total_month = str(int((today_date - join_date).days / 30))
                total_days = int((today_date - join_date).days % 30)
                employee.senior_months = total_month
                employee.senior_days = total_days
            else:
                employee.senior_months = False
                employee.senior_days = False

    # adding constrain to exchange_rate field
    # when the exchange_rate is 0 it will pop up a message
    @api.constrains('exchange_rate')
    def _check_exchange_rate(self):
        for employee in self:
            if employee.exchange_rate <= 0:
                raise ValidationError(_('Please input Exchange rate'))

    # to get exchange_rate data from configuration
    @api.model
    def default_get(self, fields):
        res = super(EmployeePayslip, self).default_get(fields)
        res['exchange_rate'] = int(self.env['ir.config_parameter'].sudo().get_param('hr_payslip_customize.exchange_rate'))
        return res