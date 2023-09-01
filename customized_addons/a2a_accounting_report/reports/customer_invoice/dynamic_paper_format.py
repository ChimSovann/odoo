from odoo import api, models

class A2AITServiceCommercialInvoice(models.AbstractModel):
    _name = 'report.a2a_accounting_report.a2a_it_service_commercial_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('a2a_accounting_report.a2a_it_service_commercial_invoice')
        if self.env.company.name == 'Kirirom Digital (Cambodia) Co,.Ltd':
            report.paperformat_id = self.env.ref('a2a_accounting_report.a4_invoice_kdc_long_footer').id
        else:
            report.paperformat_id = self.env.ref('a2a_accounting_report.a4_invoice').id
        docs = self.env['account.move'].search([('id', 'in', docids)])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
        return docargs

class A2AITServiceTaxInvoice(models.AbstractModel):
    _name = 'report.a2a_accounting_report.a2a_it_service_tax_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('a2a_accounting_report.a2a_it_service_tax_invoice')
        if self.env.company.name == 'Kirirom Digital (Cambodia) Co,.Ltd':
            report.paperformat_id = self.env.ref('a2a_accounting_report.a4_invoice_kdc_long_footer').id
        else:
            report.paperformat_id = self.env.ref('a2a_accounting_report.a4_invoice').id
        docs = self.env['account.move'].search([('id', 'in', docids)])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
        return docargs
