# -*- coding: utf-8 -*-
{
    'name': "shipment_po_created",
    'depends': ['base','purchase','purchase_request'],
    'author': "Sambath Vatana , E Sokmean",
    'summary': "Changing the string of Receipt in Purchase Order/RFQ into Shipment, "
               "Changing the string of Purchase Order inside status of Purchase Request/RFQ into PO Created",
    'data': [
        # 'security/ir.model.access.csv',
        'views/shipment_to_receipt.xml',
    ],
    'installable': True,
}
