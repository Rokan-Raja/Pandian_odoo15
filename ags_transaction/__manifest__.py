# -*- coding: utf-8 -*-
{
    'name': "ags_transaction",

    'summary': """
        """,

    'description': """
        AGS Transaction Integration
    """,

    'author': "Shore Point System Private Ltd",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ags_transaction_security.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/res_company.xml',
        'views/res_users_view.xml',
        'demo/demo.xml',

    ],
    'assets': {
        'web.assets_backend': ['ags_transaction/static/src/less/sweetalert2.css',
                               'ags_transaction/static/src/less/compare.less',
                               'ags_transaction/static/src/js/sweetalert2.js',
                               'ags_transaction/static/src/js/live_comparision.js'],

        'web.assets_qweb': ['ags_transaction/static/src/xml/live_comparision.xml'],
    },
    # only loaded in demonstration mode
    'demo': [

    ],
}
