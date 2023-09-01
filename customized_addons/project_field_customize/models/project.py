from odoo import fields, models


class Project(models.Model):
    _inherit = 'project.project'

    estimated_start_date = fields.Date("Estimated start date", help="Description: The"
                                                                    " date that estimates the project will start.")
    estimated_end_date = fields.Date("Estimated end date", help="Description: The"
                                                                " date that estimates the project will end. ")
    real_start_date = fields.Date("Real start date", help="Description: The"
                                                          " date that the project starts in real time. ")
    real_end_date = fields.Date("Real end date", help="Description: The"
                                                      " date that the project is finished in real time. ")
    estimated_cost = fields.Float("Estimated cost", help="Description: The"
                                                         " estimation of project costs. ")
    reality_cost = fields.Float("Reality cost", help="Description: The"
                                                     " reality of project costs.")
    project_status = fields.Many2one('project.status.config', "Status",
                                     help="The current status of the project.(New, In Progress, Done)")
    link = fields.Char("Link", help='Link of the Excel sheet that contains detail information of the project')
    description = fields.Text(
        'Description', translate=True, help="Description of the project in detail")
    x_code = fields.Char(string="Code", help="Project Code")
