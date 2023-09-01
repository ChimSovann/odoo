# -*- coding: utf-8 -*-
{
    'name': "activity",
    'version': "13.2.1",
    'author': "Ven Channa (B8)",
    'category': 'Activity',
    'summary': "New Module for Activity in Resort",
    'data': [
        'reports/report.xml',
        'reports/receipt_activity_header.xml',
        'reports/receipt_activity_template.xml',
        'reports/receipt_activity_footer.xml',
        'security/activity_security.xml',
        'security/ir.model.access.csv',
        'views/activity_view.xml',
    ],
    'installable': True,
    'depends': ['hotel_reservation', 'base', 'hotel', 'sale', 'purchase', 'point_of_sale'],
}
