

{
    'name': 'VK POS Dummy Orders',
    'version': '0.1',
    'author': 'Phalla Borormey',
    'category': 'Point Of Sale',
    'sequence': 31,
    'summary': 'I honestly dk what the fuck this is for but meh, not gonna hurt if we have it anw',
    'depends': ['point_of_sale'],
    'description': "",
    "data": [
        'security/ir.model.access.csv',
        'views/dummy_orders_view.xml',
        'views/dummy_orders_line_view.xml',
        'views/group_data.xml',
    ],
    "demo": [],
    'auto_install': False,
    'installable': True,
}
