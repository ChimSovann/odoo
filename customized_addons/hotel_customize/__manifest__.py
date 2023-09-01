{
    "name": "Hotel reservation customize",
    "version": "13.1.1",
    "author": "Yong Vuthivann (B8), Ven Channa (B8), Soth Sambath(B8)",
    'category': 'Hotel/Hotel reservation',
    "summary": "Customize on hotel reservation",
    "data": [
        'security/ir.model.access.csv',
        "views/hotel_reservation_customize.xml",
        "views/hotel_room_config.xml",
        "views/hotel_room_gold_day.xml",
        "views/assets.xml",
        "views/customer_type_view.xml",
        "views/country.xml",
        "views/city.xml"
    ],
    "qweb": ["static/src/xml/hotel_room_summary.xml"],
    "installable": True,
    "depends": ["hotel_reservation", "hotel"]
}