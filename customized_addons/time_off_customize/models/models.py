from odoo import models


class TimeOff(models.Model):
  _inherit = 'hr.leave'

  def get_child(self, employee):
    children = []
    if not employee.child_ids:
      return children
    for child in employee.child_ids:
      children.append(child.id)
      children += self.get_child(child)
    return children

  def action_approve_department(self):
    current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
    uid = self.env.uid

    children = self.get_child(current_employee)

    return {
      'name': 'Time Off',
      'type': 'ir.actions.act_window',
      'view_mode': 'tree,kanban,form,calendar,activity',
      'context': {"search_default_my_team_leaves": 1, "search_default_approve": 1},
      'domain': ['|', '&', ('employee_id.id', 'in', children), ('holiday_status_id.validation_type', '=', 'both'), '|',
                 '|', '&', ('employee_id.leave_manager_id', '=', uid),
                 ('holiday_status_id.validation_type', '=', 'manager'), '&',
                 ('holiday_status_id.responsible_id', '=', uid), ('holiday_status_id.validation_type', '=', 'hr'), '&',
                 '|', ('holiday_status_id.responsible_id', '=', uid), ('holiday_status_id.responsible_id', '=', uid),
                 ('holiday_status_id.validation_type', '=', 'both')],
      'res_model': 'hr.leave',
    }
