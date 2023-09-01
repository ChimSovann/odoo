# See LICENSE file for full copyright and licensing details.
{
    "name": "Inventory Stock Move Report Customize",
    "version": "13.1.2",
    "author": "Phalla Borormey(8A)",
    "category": "Inventory",
    "website": "https://docs.google.com/document/d/1sE9R9ejjUlerRwDc81nVIfH1L38XSvw__ibIO7280Qo/edit",
    "summary": "Add custom Stock Move Report function, Module needed: xlwt and XlsxWriter(pip install xlwt and pip install XlsxWriter), REQ Agreement Page: 8,9",
    'depends': ["base", "web", "stock", "product", "uom"],
    "data": [
        'wizard/stock_move_report_wizard.xml',
        'views/stock_move_report_view.xml',
    ],
    "installable": True,
}