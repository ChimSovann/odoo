from odoo import fields, models


class ProjectStatusConfig(models.Model):
    _name = 'project.status.config'

    name = fields.Char("Status")