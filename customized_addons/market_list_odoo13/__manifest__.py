# -*- coding: utf-8 -*-
{
    'name': "Market List",
    'sequence': 11,
    'summary': """
        Odoo Market-list and Purchase request management for vkirirom and A2A at
        Treng Tranyeng, REQ Agreement Page: 3-6""",

    'description': """
        Market List is the additional functional for purchase and 
        purchase request at Treng Tranyeng which benefit to company in controlling expense of food
        and beverage for employee and tracking the price of product in odoo system itself.
        """,

    'author': "Sodaney Sary (B6), DaraPichchan Huy(B8), Ratanaksambat Doung(B8), Sokchhunly Nel(B8)",
    'website': "https://drive.google.com/file/d/1lsCI9fWWujJNOEqSM-VYZZlw4ZkMYuwW/view?usp=sharing",
    'version': '13.2.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'uom', 'account', 'stock', 'mail', 'odoo_report_xlsx'],

    'data': [
        'data/market_list_data.xml',
        'data/market_list_sequence.xml',

        'security/ir.model.access.csv',
        'views/market_list_root_menu.xml',

        # market list request
        'views/market_list_request.xml',
        'views/market_list_request_pvk.xml',
        'views/market_list_request_general.xml',
        'views/market_list_request_general_view_a2a.xml',

        'views/views.xml',
        'views/templates.xml',
        'views/supplier_configuration_view.xml',
        'views/analytic_acc_for_report_config_view.xml',
        'views/purchase_order_line.xml',
        'views/purchase_order.xml',
        'views/survey_price.xml',
        'views/order_statistics.xml',
        'views/report_statistics.xml',

        # report
        'reports/paper_format.xml',
        'reports/report.xml',
        'reports/custom_report_layout.xml',
        'reports/market_list_request_report.xml',
        'reports/purchase_order_report.xml',
        'reports/payment_voucher_report.xml',
        'reports/pvk_request_report.xml',
        'reports/market_list_request_general_a2a_report.xml',

        'reports/supplier_payment_voucher_form.xml',
        'reports/purchase_payment_template.xml',
        'reports/general_request_report.xml',
        'reports/purchase_payment_account_template.xml',

        # wizard
        'wizard/supplier_payment_report_wizard.xml',
        'wizard/payment_report_wizard.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
