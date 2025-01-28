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
        #'security/ir.model.access.csv',
        'views/account_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'installable': True,
    'application': True,
}
