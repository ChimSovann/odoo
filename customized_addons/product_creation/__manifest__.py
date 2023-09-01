{
    'name': "Product Creation",

    'summary': """
        Create a Product Creation Group
    """,

    'description': """
        Create a new user group with access rights to create the products.
    """,

    'author': "Sambath Soth",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'product', 'sale'],

    'data': [
        'security/product_creation_security.xml',
        'security/ir.model.access.csv',
    ],
}
