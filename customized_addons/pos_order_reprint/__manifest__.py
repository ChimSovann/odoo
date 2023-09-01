{
    "name": "POS Reprint Receipt",
    "summary": "Manage old POS Orders from the frontend and reprint it, also print double receipt functionality",
    "version": "13.2.1",
    "category": "Point of Sale",
    "author": "Sambath Soth (B8), reference GRAP, " "Tecnativa, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/pos",
    "license": "AGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "views/assets.xml",
        "views/view_pos_config.xml",
    ],
    "qweb": [
        "static/src/xml/pos.xml",
        "static/src/xml/pos_receipt.xml",
    ],
    "application": False,
    "installable": True,
}
