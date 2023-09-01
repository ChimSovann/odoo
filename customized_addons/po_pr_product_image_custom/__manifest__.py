# -*- coding: utf-8 -*-
{
    'name': "po_pr_product_image_custom",
    'version': '13.2.1',
    'category': 'Purchase, Purchase Request',
    'author': ["Sambath Vatana (B8)", "E Sokmean (B8)"],
    'website': 'https://docs.google.com/document/d/1uI5U9cjFtqly-3zb1xDGYpkuz_5hHy3a/edit',
    'summary': "Implement a small image of each product into Purchase Request/RFQ/Purchase Order, REQ Agreement Page: 3",
    'depends': ['base', 'purchase', 'purchase_request'],

    'data': [
        'views/po_views.xml',
        'views/pr_views.xml',
        'views/templates.xml',
    ],
    'installable': True,
}
