# -*- coding: utf-8 -*-

{
    'name'        : 'Brazilian eInvoicing & Payments Extension',
    'version'     : '1.0',
    "license"     : "AGPL-3",
    'author'      : '',
    'website'     : '',
    'category'    : 'Account',
    'summary'     : 'Extension of eInvoicing & Payments Module',
    'description' : """

Improvements for eInvoicing & Payments Module:
    * Period bug fix when Company is changed (multi-company)

""",
    'depends'     : ['l10n_br_account_voucher'],
    'data'        : ['voucher_payment_receipt_view.xml'],
    'demo'        : [],
    'test'        : [],
    'installable' : True,
    'auto_install': True,
    'application' : False,
}
