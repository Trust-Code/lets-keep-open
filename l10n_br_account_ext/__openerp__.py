# -*- coding: utf-8 -*-

{
    'name'        : 'Brazilian Account Extension',
    'version'     : '002.08',
    "license"     : "AGPL-3",
    'author'      : '',
    'website'     : '',
    'category'    : 'Account',
    'sequence'    : 14,
    'summary'     : 'Extension of Account and Financial Module',
    'description' : """

Improvements for Accounting and Financial Module:

    * Show date maturity on invoice
    * Allow immediate payment
    * Create Electronic Invoice Description in Service Type
    * Ajust Invoice Accounting

""",
    'depends'     : ['l10n_br_account',
                     'l10n_br_account_voucher',
                     'l10n_br_purchase',
                     'l10n_br_stock',],
    'data'        : ['account_view.xml',
                     'account_invoice_view.xml',
                     'account_invoice_workflow.xml',],
    'demo'        : [],
    'test'        : [],
    'installable' : True,
    'auto_install': False,
    'application' : False,
}
