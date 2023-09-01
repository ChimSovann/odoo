{
    "name": "HLS Integration",
    "version": "13.2.1",
    "author": "Sambath Soth (B8)",
    "website": "https://docs.google.com/document/d/1O3dE5Z93qx9kn60kKuHGCJSWxeZ63Myg/edit",
    "summary": 'Integration Hotel Reservation with HLS (Hotel Link Solution), REQ Agreement Page: 3',
    "category": 'Hotel',
    'depends': [
        'base',
        'hotel',
        'hotel_reservation',
    ],
    'data': [
        'security/hls_hotel_reservation_integration_security.xml',
        'security/ir.model.access.csv',
        'views/hls_hotel_reservation_config_view.xml',
        'views/product_category_form_view_inherit.xml',
        'views/hotel_reservation_form_view_inherit.xml',
        'views/hls_cron_job.xml',
        'wizards/wizard_message_view.xml',
    ],
}
