{
  'name': 'Accounting Customization',
  'version': '13.3.01',
  'category': 'Accounting',
  'author': 'Reth Sokmeta(B8), Thy Saonan(B8), Meng Vengsokun(B8)',
  'summary': '''Add new custom fields on vendor bill, 
                Customer invoice/vendor bill register payment and Product categories, 
                Add activity log to journal entries and add new customer discount functionality. 
                Requirement Agreeement Page: 3,4,6,7,8''',
  'website': 'https://docs.google.com/document/d/1BzFCpYVMn_hsKkT7A2cCzyCqhN5ytPrSaeNFpKMo8Qk',
  'depends': ['sale', 'account', 'account_parent', 'point_of_sale', 'account_asset_management', 'partner_firstname'],
  'data': [
    'views/customer_invoice_tree.xml',
    'views/journal_entries_customize_view.xml',
    'views/product_category_customize_view.xml',
    'views/vendor_bill_customize_view.xml',
    'views/coa_customize_view.xml',
    'views/discount_customize_view.xml',
    'views/asset_management_customize.xml',
    'views/bank_statement_customize.xml',
    'views/res_partner_customize.xml',
    'views/account_payment_customize.xml'
  ],
  'installable': True,
  'qweb': [
    'static/src/xml/parent_line.xml',
  ],
}
