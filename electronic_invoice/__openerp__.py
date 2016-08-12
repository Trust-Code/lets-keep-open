# -*- coding: utf-8 -*-


{
    'name'        : 'Brazilian Electronic Invoice',
    'version'     : '002.11',
    "license"     : "AGPL-3",
    'author'      : '',
    'website'     : '',
    'category'    : 'Account',
    'sequence'    : 10,
    'summary'     : 'Brazilian Electronic Invoice',
    'description' : """

Service Electronic Invoice:

    * Send Electronic Invoice (RPS)
    * Cancel Electronic Invoice
    * Update Electronic Invoice

""",
    'depends'     : ['l10n_br_base_ext',
                     'l10n_br_account_ext',
                     'l10n_br_product_ext',
                     'l10n_br_sale',],
    'data'        : ['wizard/eletronic_invoice_wizard_view.xml',
                     'wizard/danfe_join_view.xml',
                     'account_invoice_view.xml',
                     'l10n_br_account_view.xml',
                     'res_company_view.xml',
                     'res_partner_view.xml',
                     'schedule_data_view.xml',
                     'eletronic_invoice_sequence.xml'
                     ],
    'demo'        : [],
    'test'        : [],
    'installable' : True,
    'auto_install': False,
    'application' : False,
}
