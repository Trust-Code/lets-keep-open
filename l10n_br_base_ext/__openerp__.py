# -*- coding: utf-8 -*-

{
    'name'        : 'Brazilian Base Extension',
    'version'     : '001.05',
    'license'     : 'AGPL-3',
    'author'      : '',
    'website'     : '',
    'category'    : 'Account',
    'sequence'    : 14,
    'summary'     : 'Extension of Base Module',
    'description' : """

Improvements for Base Module:

    * Show default partner receivable account
    * Show default partner payable account
    * Show default partner fiscal type

""",
    'depends'     : ['l10n_br_base',
                     'l10n_br_account',
                     'l10n_br_stock',
                     'l10n_br_purchase',],
    'data'        : ['res_company_view.xml'],
#                     'res_partner.xml'
    'demo'        : [],
    'test'        : [],
    'installable' : True,
    'auto_install': False,
    'application' : False,
}
