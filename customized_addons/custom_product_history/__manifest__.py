# -*- coding: utf-8 -*-
{
    'name': "custom_product_history",
    'version': '13.2.1',
    'category': 'Purchase',
    'author': ["Sambath Vatana (B8)", "E Sokmean (B8)"],
    'website': 'https://docs.google.com/document/d/1uI5U9cjFtqly-3zb1xDGYpkuz_5hHy3a/edit',
    'depends': ['base', 'purchase', 'purchase_request', 'sale', 'account', 'stock'],
    'summary': "Display Purchase History of each product in tree views, REQ Agreement Page: 7,8",
    'data': [
        'views/product_history_view.xml',
    ],
    'installable': True,
}
