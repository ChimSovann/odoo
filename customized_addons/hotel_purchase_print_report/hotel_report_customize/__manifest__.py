{
    "name": "FO Daily Report Customize",
    "version": "13.2.1",
    "author": "Yong Vuthivann (B8), Ven Channa (B8)",
    "category": 'Hotel',
    "website": "https://docs.google.com/document/d/1O3dE5Z93qx9kn60kKuHGCJSWxeZ63Myg/edit",
    "summary": """
        Customize on FO daily report Template
    """,
    'depends': ['base', 'hotel', 'hotel_restaurant', 'hotel_folio', 'hotel_reservation'],
    'data': [
        'views/report_customize.xml',
        'views/report_template_customize.xml',
        'views/report_wizard_inherit.xml',
        'views/report_header.xml'
    ],
}
