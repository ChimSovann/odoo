{
    "name": "Hotel Folio & Invoice",
    "version": "13.2.1",
    "author": "Yong Vuthivann (B8), Ven Channa (B8), Sambath Soth (B8)",
    "category": 'Hotel',
    "website": "https://docs.google.com/document/d/1O3dE5Z93qx9kn60kKuHGCJSWxeZ63Myg/edit",
    "summary": """
    Customize folio generation tree view, form view and add some new field, REQ Agreement Page: 3,4,5.
    Customize on Invoice, adding fields, adding Notebook and adding wizard exactly the same as Odoo 8 (Old version).
    """,
    'depends': ['base', 'hotel', 'hotel_reservation', 'product'],
    'data': [
        'views/folio_room_line_view.xml',
        'views/hotel_folio_customize_view.xml',
    ],
}
