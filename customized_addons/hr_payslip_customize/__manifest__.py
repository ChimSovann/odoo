# See LICENSE file for full copyright and licensing details.

{
    "name": "Hr Payslip Customize",
    "version": "13.1.3",
    "category": 'Employees',
    "author": "Thon Lynan",
    "website": "https://docs.google.com/document/d/1-8BFWtZtrHnuFxUeyWFOE1otPedMnmcGlETRqi8a5HQ/edit",
    "summary": "Manage employee payslip by adding fields to calculate payslip base on government requirement,"
               "REQ Agreement Page: 5-8",
    "depends": [
        'om_hr_payroll',
    ],
    "data": [
        'view/employee_payslip.xml',
        'view/setting.xml',
        'reports/report_payslip_customize.xml'
    ],
    "installable": True,
}
