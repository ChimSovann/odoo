# -*- coding: utf-8 -*-
{
    'name': "custom_pr_no",
    'version': '13.3.1',
    'category': 'Purchase',
    'author': ["Sambath Vatana (B8)", "E Sokmean (B8)"],
    'website': 'https://docs.google.com/document/d/1uI5U9cjFtqly-3zb1xDGYpkuz_5hHy3a/edit, https://docs.google.com/document/d/1cjiIhkGyZJa-bVyS-OpBy5wWEw_Y8XRf/edit',
    'depends': ['base', 'purchase', 'purchase_request', 'stock', 'purchase_deposit'],
    'summary': "Automate PR No, Changing Receipt -> Shipmernt and Adding important fields into Purchase Request/Purchase Order/RFQ inside form view, REQ Agreement Page4, 5, 6",
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/filter_customized_view.xml',
        'views/po_tree.xml',
        'views/rfq_form.xml',
        'views/rfq_tree.xml',
        'views/purchase_request_tree.xml',
        'views/purchase_request_form.xml',
        'views/pr_wrap_text.xml',
        'views/po_wrap_text.xml',
        'views/vendor_customize.xml',
        'views/route_view.xml',
        'views/route_form_view.xml',
    ],
    'installable': True,
}
