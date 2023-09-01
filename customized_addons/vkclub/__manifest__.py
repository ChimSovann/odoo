{
    'name': "VkClub Pos Integration",
    'summary': "This application objective is to integrate vkclub into POS to allow vkclub transaction via POS.",
    'description': """
            Allow Payment with VKPoint
            Main Features:
            --------------
            * Add VKPoint Payment Button to POS
            * Add QRCode to receipt to provide easy way for payment 
            * Add Exchange rate from Dollar to VKPoint
            * Adding Vk balance report
            * Posting transaction to VkClub backend server ( Currently Using Odoo 12 )
                       """,
    'author': "Phalla Borormey",
    'website': 'https://www.vkirirom.com',
    'version': "1.0",
    'category': 'Point Of Sale',
    'depends': ['point_of_sale', 'vk_dummy_pos_order', 'web', 'base', 'mail'],
    'data': ['security/ir.model.access.csv',
             'reports/vk_balance_report.xml',
             'views/vk_pos_view.xml',
             'views/template.xml',
             'views/vk_pos_payment_method.xml',


             ],
    'qweb': [
        'static/src/xml/data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}