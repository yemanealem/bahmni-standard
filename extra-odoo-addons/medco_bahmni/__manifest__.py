# -*- coding: utf-8 -*-
{
    'name': "Medco Bahmni Integration",

    'summary': """
        Medco Bahmni integration""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Medco PLC",
    'website': "https://www.com",

    
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'data/claim_sequence.xml', 
        'security/ir.model.access.csv',
        'views/account_inherit.xml',
        'views/account_view_inherited_invoice_tree.xml',
        'views/medco_bhamni_menu.xml',
        'views/claim_view.xml',
        'views/res_partner_view.xml'
        # 'views/account_move_sale_inherited.xml'
        
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'installable': True,
    'application': True,
}
