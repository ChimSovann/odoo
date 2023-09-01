# -*- coding: utf-8 -*-
{
    'name': "Pos Hotel Folio Integration",

    'summary': """
        This module is used to integrate the hotel folio with the pos order.""",

    'description': """
        This module is used to create a button that allow the user to select a hotel folio 
        and sent all the order to the selected folio.
    """,

    'author': "Sambath Soth (B8)",
    'website': "http://www.yourcompany.com",

    'category': 'Point of Sale',
    'version': '13.3.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'hotel', 'pos_product_available'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_config_form_view_inherit.xml',
    ],

    'qweb': [
        'static/src/xml/pos_folio.xml',
    ],
}
